use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Serialize, Deserialize, Clone, Debug)]
#[serde(rename_all = "snake_case")]
pub enum PaymentStatus {
    Pending,
    Authorized,
    Captured,
    Failed,
    Refunded,
}

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct Pago {
    pub _id: String,       // usamos UUID string
    pub trip_id: String,
    pub user_id: String,
    pub amount: f64,
    pub currency: String,
    pub method: String,    // "card" | "wallet"
    pub status: PaymentStatus,
    pub idempotency_key: Option<String>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

impl Pago {
    pub fn new(trip_id: String, user_id: String, amount: f64, currency: String, method: String, idempotency_key: Option<String>) -> Self {
        let now = Utc::now();
        Self {
            _id: Uuid::new_v4().to_string(),
            trip_id,
            user_id,
            amount,
            currency,
            method,
            status: PaymentStatus::Captured, // para demo “capturamos” directo
            idempotency_key,
            created_at: now,
            updated_at: now,
        }
    }
}

#[derive(Deserialize)]
pub struct CreatePagoDTO {
    pub trip_id: String,
    pub amount: f64,
    #[serde(default = "default_currency")]
    pub currency: String,
    #[serde(default = "default_method")]
    pub method: String,
}

fn default_currency() -> String { "BOB".into() }
fn default_method() -> String { "card".into() }

#[derive(Serialize)]
pub struct PagoCreatedResp {
    pub payment_id: String,
    pub status: PaymentStatus,
}

#[derive(Serialize)]
pub struct PagoDetailResp {
    pub payment: Pago,
}
