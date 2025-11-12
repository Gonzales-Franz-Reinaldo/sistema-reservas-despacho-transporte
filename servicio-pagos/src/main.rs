mod config;
mod db;
mod models;
mod routes;
mod services;

use actix_cors::Cors;
use actix_web::{middleware::Logger, App, HttpServer};
use config::Settings;
use db::DbState;
use routes::init_routes;
use std::sync::Arc;

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    env_logger::init();
    let settings = Settings::from_env().expect("Error cargando configuración");
    let db = DbState::connect(&settings.mongo_uri, &settings.database_name)
        .await
        .expect("No se pudo conectar a Mongo");

    let shared_db = Arc::new(db);
    let port = settings.port;

    println!("[pagos] escuchando en 0.0.0.0:{port}");

    HttpServer::new(move || {
        let cors = if settings.cors_origins == "*" {
            Cors::permissive()
        } else {
            let mut c = Cors::default();
            for o in settings.cors_origins.split(',') {
                c = c.allowed_origin(o.trim());
            }
            c.allowed_methods(vec!["GET", "POST", "PUT", "DELETE", "OPTIONS"])
                .allowed_headers(vec![
                    actix_web::http::header::AUTHORIZATION,
                    actix_web::http::header::CONTENT_TYPE,
                    actix_web::http::header::HeaderName::from_static("idempotency-key"),
                ])
                .supports_credentials()
        };

        App::new()
            .app_data(actix_web::web::Data::new(shared_db.clone()))
            .app_data(actix_web::web::Data::new(settings.clone()))
            .wrap(Logger::default())
            .wrap(cors)
            .configure(init_routes)
    })
    .bind(("0.0.0.0", port))?
    .run()
    .await
}
