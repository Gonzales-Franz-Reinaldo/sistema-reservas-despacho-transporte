use actix_web::web;
mod health;
mod pagos;

pub fn init_routes(cfg: &mut web::ServiceConfig) {
    cfg
        .service(health::scope())
        .service(pagos::scope());
}
