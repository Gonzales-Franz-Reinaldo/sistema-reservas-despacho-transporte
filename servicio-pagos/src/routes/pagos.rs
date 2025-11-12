use actix_web::{web, HttpResponse, Scope};
use mongodb::bson::doc;

use crate::{
    config::Settings,
    db::DbState,
    models::pago::{CreatePagoDTO},
    services::{jwt::{decode_jwt, extract_bearer}, pagos_service::PagosService},
};

pub fn scope() -> Scope {
    web::scope("/api/pagos")
        .route("", web::post().to(crear_pago))
        .route("/{id}", web::get().to(detalle_pago))
        .route("", web::get().to(listar_por_trip))
}

async fn crear_pago(
    req: actix_web::HttpRequest,
    db: web::Data<std::sync::Arc<DbState>>,
    settings: web::Data<Settings>,
    body: web::Json<CreatePagoDTO>,
) -> actix_web::Result<HttpResponse> {
    let token = extract_bearer(&req)?;
    let claims = decode_jwt(&token, &settings)?;
    let idem = req
        .headers()
        .get("idempotency-key")
        .and_then(|v| v.to_str().ok())
        .map(|s| s.to_string());

    let pagos = PagosService::new(db.db.collection("pagos"));
    let resp = pagos
        .crear_pago(claims.sub, body.into_inner(), idem)
        .await?;

    // Hook para publicar evento (cuando conectes RabbitMQ):
    // publish_payment_processed(resp.payment_id, ...).await?;

    Ok(HttpResponse::Ok().json(resp))
}

async fn detalle_pago(
    req: actix_web::HttpRequest,
    db: web::Data<std::sync::Arc<DbState>>,
    settings: web::Data<Settings>,
    path: web::Path<String>,
) -> actix_web::Result<HttpResponse> {
    let token = extract_bearer(&req)?;
    let _claims = decode_jwt(&token, &settings)?;
    let id = path.into_inner();
    let pagos = PagosService::new(db.db.collection("pagos"));
    match pagos.detalle(&id).await? {
        Some(detail) => Ok(HttpResponse::Ok().json(detail)),
        None => Ok(HttpResponse::NotFound().finish()),
    }
}

#[derive(serde::Deserialize)]
struct ListQuery {
    trip_id: String,
}

async fn listar_por_trip(
    req: actix_web::HttpRequest,
    db: web::Data<std::sync::Arc<DbState>>,
    settings: web::Data<Settings>,
    q: web::Query<ListQuery>,
) -> actix_web::Result<HttpResponse> {
    let token = extract_bearer(&req)?;
    let _claims = decode_jwt(&token, &settings)?;
    let pagos = PagosService::new(db.db.collection("pagos"));
    let lista = pagos.find_by_trip(&q.trip_id).await?;
    Ok(HttpResponse::Ok().json(serde_json::json!({ "items": lista })))
}
