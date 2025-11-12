// src/services/jwt.rs
use actix_web::{HttpRequest};
use actix_web::error::Error as ActixError;
use jsonwebtoken::{decode, DecodingKey, Validation, Algorithm};
use serde::{Deserialize, Serialize};

use crate::config::Settings;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Claims {
    pub sub: String,       // user_id
    pub exp: usize,        // timestamp (segundos)
    pub role: Option<String>,
    pub scope: Option<String>,
}

/// EXTRAER "Bearer <token>" DEL HEADER Authorization DESDE HttpRequest
pub fn extract_bearer(req: &HttpRequest) -> Result<String, ActixError> {
    let auth = req
        .headers()
        .get("Authorization")
        .ok_or_else(|| actix_web::error::ErrorUnauthorized("Missing Authorization header"))?
        .to_str()
        .map_err(|_| actix_web::error::ErrorUnauthorized("Invalid Authorization header"))?;

    if let Some(tok) = auth.strip_prefix("Bearer ").or_else(|| auth.strip_prefix("bearer ")) {
        Ok(tok.trim().to_string())
    } else {
        Err(actix_web::error::ErrorUnauthorized("Expected Bearer token"))
    }
}

/// DECODIFICAR JWT (HS256 o RS256 según settings)
pub fn decode_jwt(token: &str, settings: &Settings) -> Result<Claims, ActixError> {
    let alg = match settings.jwt_alg.as_str() {
        "RS256" => Algorithm::RS256,
        _       => Algorithm::HS256,
    };

    match alg {
        Algorithm::HS256 => {
            let secret = settings
                .jwt_secret
                .as_ref()
                .ok_or_else(|| actix_web::error::ErrorInternalServerError("JWT_SECRET missing"))?;
            let mut validation = Validation::new(Algorithm::HS256);
            validation.validate_exp = true;
            let data = decode::<Claims>(token, &DecodingKey::from_secret(secret.as_bytes()), &validation)
                .map_err(|e| actix_web::error::ErrorUnauthorized(format!("Invalid token: {e}")))?;
            Ok(data.claims)
        }
        Algorithm::RS256 => {
            let pub_pem = settings.jwt_public_pem.as_ref()
                .ok_or_else(|| actix_web::error::ErrorInternalServerError("JWT_PUBLIC_KEY_PEM missing"))?;
            let mut validation = Validation::new(Algorithm::RS256);
            validation.validate_exp = true;
            let data = decode::<Claims>(token, &DecodingKey::from_rsa_pem(pub_pem.as_bytes()).map_err(|e|
                actix_web::error::ErrorInternalServerError(format!("Bad RSA public key: {e}"))
            )?, &validation)
                .map_err(|e| actix_web::error::ErrorUnauthorized(format!("Invalid token: {e}")))?;
            Ok(data.claims)
        }
        _ => Err(actix_web::error::ErrorInternalServerError("Unsupported JWT_ALG")),
    }
}
