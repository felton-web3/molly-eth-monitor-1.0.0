//! Email notification implementation.
//!
//! Provides functionality to send formatted messages to email addresses
//! via SMTP, supporting message templates with variable substitution.

use async_trait::async_trait;
use email_address::EmailAddress;
use lettre::{
	message::{
		header::{self, ContentType},
		Mailbox, Mailboxes,
	},
	Message, SmtpTransport, Transport,
};
use std::{collections::HashMap, sync::Arc};

use crate::{
	models::TriggerTypeConfig,
	services::notification::{NotificationError, Notifier},
};
use pulldown_cmark::{html, Options, Parser};

/// Implementation of email notifications via SMTP
#[derive(Debug)]
pub struct EmailNotifier<T: Transport + Send + Sync> {
	/// Email subject
	subject: String,
	/// Message template with variable placeholders
	body_template: String,
	/// SMTP client for email delivery
	client: T,
	/// Email sender
	sender: EmailAddress,
	/// Email recipients
	recipients: Vec<EmailAddress>,
}

/// Configuration for SMTP connection
#[derive(Clone, Debug, Hash, Eq, PartialEq)]
pub struct SmtpConfig {
	pub host: String,
	pub port: u16,
	pub username: String,
	pub password: String,
}

/// Configuration for email content
#[derive(Clone)]
pub struct EmailContent {
	pub subject: String,
	pub body_template: String,
	pub sender: EmailAddress,
	pub recipients: Vec<EmailAddress>,
}

impl<T: Transport + Send + Sync> EmailNotifier<T>
where
	T::Error: std::fmt::Display,
{
	/// Creates a new email notifier instance with a custom transport
	///
	/// # Arguments
	/// * `email_content` - Email content configuration
	/// * `transport` - SMTP transport
	///
	/// # Returns
	/// * `Self` - Email notifier instance
	pub fn with_transport(email_content: EmailContent, transport: T) -> Self {
		Self {
			subject: email_content.subject,
			body_template: email_content.body_template,
			sender: email_content.sender,
			recipients: email_content.recipients,
			client: transport,
		}
	}
}

impl EmailNotifier<SmtpTransport> {
	/// Creates a new email notifier instance
	///
	/// # Arguments
	/// * `smtp_client` - SMTP client
	/// * `email_content` - Email content configuration
	///
	/// # Returns
	/// * `Result<Self, NotificationError>` - Email notifier instance or error
	pub fn new(
		smtp_client: Arc<SmtpTransport>,
		email_content: EmailContent,
	) -> Result<Self, NotificationError> {
		Ok(Self {
			subject: email_content.subject,
			body_template: email_content.body_template,
			sender: email_content.sender,
			recipients: email_content.recipients,
			client: smtp_client.as_ref().clone(),
		})
	}

	/// Formats a message by substituting variables in the template and converts it to HTML
	///
	/// # Arguments
	/// * `variables` - Map of variable names to values
	///
	/// # Returns
	/// * `String` - Formatted message with variables replaced and converted to HTML
	pub fn format_message(&self, variables: &HashMap<String, String>) -> String {
		let formatted_message = variables
			.iter()
			.fold(self.body_template.clone(), |message, (key, value)| {
				message.replace(&format!("${{{}}}", key), value)
			});

		Self::markdown_to_html(&formatted_message)
	}

	/// Convert a Markdown string into HTML
	pub fn markdown_to_html(md: &str) -> String {
		// enable all the extensions you like; or just Parser::new(md) for pure CommonMark
		let opts = Options::all();
		let parser = Parser::new_ext(md, opts);

		let mut html_out = String::new();
		html::push_html(&mut html_out, parser);
		html_out
	}

	/// Creates an email notifier from a trigger configuration
	///
	/// # Arguments
	/// * `config` - Trigger configuration containing email parameters
	///
	/// # Returns
	/// * `Result<Self, NotificationError>` - Notifier instance if config is email type
	pub fn from_config(
		config: &TriggerTypeConfig,
		smtp_client: Arc<SmtpTransport>,
	) -> Result<Self, NotificationError> {
		if let TriggerTypeConfig::Email {
			message,
			sender,
			recipients,
			..
		} = config
		{
			let email_content = EmailContent {
				subject: message.title.clone(),
				body_template: message.body.clone(),
				sender: sender.clone(),
				recipients: recipients.clone(),
			};

			Self::new(smtp_client, email_content)
		} else {
			Err(NotificationError::config_error(
				format!("Invalid email configuration: {:?}", config),
				None,
				None,
			))
		}
	}
}

#[async_trait]
impl<T: Transport + Send + Sync> Notifier for EmailNotifier<T>
where
	T::Error: std::fmt::Display,
{
	/// Sends a formatted message to email
	///
	/// # Arguments
	/// * `message` - The formatted message to send
	///
	/// # Returns
	/// * `Result<(), NotificationError>` - Success or error
	async fn notify(&self, message: &str) -> Result<(), NotificationError> {
		let recipients_str = self
			.recipients
			.iter()
			.map(ToString::to_string)
			.collect::<Vec<_>>()
			.join(", ");

		let mailboxes: Mailboxes = recipients_str.parse::<Mailboxes>().map_err(|e| {
			NotificationError::notify_failed(
				format!("Failed to parse recipients: {}", e),
				Some(e.into()),
				None,
			)
		})?;
		let recipients_header: header::To = mailboxes.into();

		let email = Message::builder()
			.mailbox(recipients_header)
			.from(self.sender.to_string().parse::<Mailbox>().map_err(|e| {
				NotificationError::notify_failed(
					format!("Failed to parse sender: {}", e),
					Some(e.into()),
					None,
				)
			})?)
			.reply_to(self.sender.to_string().parse::<Mailbox>().map_err(|e| {
				NotificationError::notify_failed(
					format!("Failed to parse reply-to: {}", e),
					Some(e.into()),
					None,
				)
			})?)
			.subject(&self.subject)
			.header(ContentType::TEXT_HTML)
			.body(message.to_owned())
			.map_err(|e| {
				NotificationError::notify_failed(
					format!("Failed to build email message: {}", e),
					Some(e.into()),
					None,
				)
			})?;

		self.client.send(&email).map_err(|e| {
			NotificationError::notify_failed(format!("Failed to send email: {}", e), None, None)
		})?;

		Ok(())
	}
}

#[cfg(test)]
mod tests {
	use lettre::transport::smtp::authentication::Credentials;

	use crate::{
		models::{NotificationMessage, SecretString, SecretValue},
		services::notification::pool::NotificationClientPool,
	};

	use super::*;

	fn create_test_notifier() -> EmailNotifier<SmtpTransport> {
		let smtp_config = SmtpConfig {
			host: "dummy.smtp.com".to_string(),
			port: 465,
			username: "test".to_string(),
			password: "test".to_string(),
		};

		let client = SmtpTransport::relay(&smtp_config.host)
			.unwrap()
			.port(smtp_config.port)
			.credentials(Credentials::new(smtp_config.username, smtp_config.password))
			.build();

		let email_content = EmailContent {
			subject: "Test Subject".to_string(),
			body_template: "Hello ${name}, your balance is ${balance}".to_string(),
			sender: "sender@test.com".parse().unwrap(),
			recipients: vec!["recipient@test.com".parse().unwrap()],
		};

		EmailNotifier::new(Arc::new(client), email_content).unwrap()
	}

	fn create_test_email_config(port: Option<u16>) -> TriggerTypeConfig {
		TriggerTypeConfig::Email {
			host: "smtp.test.com".to_string(),
			port,
			username: SecretValue::Plain(SecretString::new("testuser".to_string())),
			password: SecretValue::Plain(SecretString::new("testpass".to_string())),
			message: NotificationMessage {
				title: "Test Subject".to_string(),
				body: "Hello ${name}".to_string(),
			},
			sender: "sender@test.com".parse().unwrap(),
			recipients: vec!["recipient@test.com".parse().unwrap()],
		}
	}

	////////////////////////////////////////////////////////////
	// format_message tests
	////////////////////////////////////////////////////////////

	#[test]
	fn test_format_message_basic_substitution() {
		let notifier = create_test_notifier();
		let mut variables = HashMap::new();
		variables.insert("name".to_string(), "Alice".to_string());
		variables.insert("balance".to_string(), "100".to_string());

		let result = notifier.format_message(&variables);
		let expected_result = "<p>Hello Alice, your balance is 100</p>\n";
		assert_eq!(result, expected_result);
	}

	#[test]
	fn test_format_message_missing_variable() {
		let notifier = create_test_notifier();
		let mut variables = HashMap::new();
		variables.insert("name".to_string(), "Bob".to_string());

		let result = notifier.format_message(&variables);
		let expected_result = "<p>Hello Bob, your balance is ${balance}</p>\n";
		assert_eq!(result, expected_result);
	}

	#[test]
	fn test_format_message_empty_variables() {
		let notifier = create_test_notifier();
		let variables = HashMap::new();

		let result = notifier.format_message(&variables);
		let expected_result = "<p>Hello ${name}, your balance is ${balance}</p>\n";
		assert_eq!(result, expected_result);
	}

	#[test]
	fn test_format_message_with_empty_values() {
		let notifier = create_test_notifier();
		let mut variables = HashMap::new();
		variables.insert("name".to_string(), "".to_string());
		variables.insert("balance".to_string(), "".to_string());

		let result = notifier.format_message(&variables);
		let expected_result = "<p>Hello , your balance is</p>\n";
		assert_eq!(result, expected_result);
	}

	////////////////////////////////////////////////////////////
	// from_config tests
	////////////////////////////////////////////////////////////

	#[tokio::test]
	async fn test_from_config_valid_email_config() {
		let config = create_test_email_config(Some(587));
		let smtp_config = match &config {
			TriggerTypeConfig::Email {
				host,
				port,
				username,
				password,
				..
			} => SmtpConfig {
				host: host.clone(),
				port: port.unwrap_or(587),
				username: username.to_string(),
				password: password.to_string(),
			},
			_ => panic!("Expected Email config"),
		};
		let pool = NotificationClientPool::new();
		let smtp_client = pool.get_or_create_smtp_client(&smtp_config).await.unwrap();
		let notifier = EmailNotifier::from_config(&config, smtp_client);
		assert!(notifier.is_ok());

		let notifier = notifier.unwrap();
		assert_eq!(notifier.subject, "Test Subject");
		assert_eq!(notifier.body_template, "Hello ${name}");
		assert_eq!(notifier.sender.to_string(), "sender@test.com");
		assert_eq!(notifier.recipients.len(), 1);
		assert_eq!(notifier.recipients[0].to_string(), "recipient@test.com");
	}

	#[tokio::test]
	async fn test_from_config_default_port() {
		let config = create_test_email_config(None);
		let smtp_config = match &config {
			TriggerTypeConfig::Email {
				host,
				port,
				username,
				password,
				..
			} => SmtpConfig {
				host: host.clone(),
				port: port.unwrap_or(587),
				username: username.to_string(),
				password: password.to_string(),
			},
			_ => panic!("Expected Email config"),
		};
		let pool = NotificationClientPool::new();
		let smtp_client = pool.get_or_create_smtp_client(&smtp_config).await.unwrap();
		let notifier = EmailNotifier::from_config(&config, smtp_client);
		assert!(notifier.is_ok());
	}

	////////////////////////////////////////////////////////////
	// notify tests
	////////////////////////////////////////////////////////////

	#[tokio::test]
	async fn test_notify_failure() {
		let notifier = create_test_notifier();
		let result = notifier.notify("Test message").await;
		// Expected to fail since we're using a dummy SMTP server
		assert!(result.is_err());

		let error = result.unwrap_err();
		assert!(matches!(error, NotificationError::NotifyFailed { .. }));
	}
}
