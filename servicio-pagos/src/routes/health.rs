use actix_web::{get, web, HttpResponse, Scope};

#[get("/health")]
async fn health() -> HttpResponse {
    HttpResponse::Ok().body("OK")
}

pub fn scope() -> Scope {
    web::scope("").service(health)
}
