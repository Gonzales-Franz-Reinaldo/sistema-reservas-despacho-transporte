use std::env;

#[derive(Clone)]
pub struct Settings {
    pub port: u16,
    pub mongo_uri: String,
    pub database_name: String,
    pub jwt_alg: String,           // HS256 o RS256
    pub jwt_secret: Option<String>,// si HS256
    pub jwt_public_pem: Option<String>, // si RS256
    pub cors_origins: String,
}

impl Settings {
    pub fn from_env() -> Result<Self, String> {
        let port = env::var("PORT").unwrap_or_else(|_| "8080".to_string())
            .parse::<u16>().map_err(|e| e.to_string())?;

        let mongo_uri = env::var("MONGO_URI").unwrap_or_else(|_| "mongodb://localhost:27017".into());
        let database_name = env::var("DATABASE_NAME").unwrap_or_else(|_| "pagos_db".into());
        let jwt_alg = env::var("JWT_ALG").unwrap_or_else(|_| "HS256".into());
        let jwt_secret = env::var("JWT_SECRET").ok();
        let jwt_public_pem = env::var("JWT_PUBLIC_KEY_PEM").ok();
        let cors_origins = env::var("CORS_ORIGINS").unwrap_or_else(|_| "*".into());

        Ok(Self {
            port,
            mongo_uri,
            database_name,
            jwt_alg,
            jwt_secret,
            jwt_public_pem,
            cors_origins,
        })
    }
}
