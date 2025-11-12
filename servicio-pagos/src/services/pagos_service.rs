use mongodb::bson::{doc, to_document};
use mongodb::Collection;
use futures::TryStreamExt; // <- añade esta línea

use crate::models::pago::{Pago, CreatePagoDTO, PagoCreatedResp, PagoDetailResp};

pub struct PagosService {
    collection: Collection<mongodb::bson::Document>,
}

impl PagosService {
    pub fn new(collection: Collection<mongodb::bson::Document>) -> Self {
        Self { collection }
    }

    pub async fn crear_pago(
        &self,
        user_id: String,
        dto: CreatePagoDTO,
        idempotency_key: Option<String>,
    ) -> Result<PagoCreatedResp, actix_web::Error> {
        // idempotencia: si llega misma key, devolvemos lo que ya existe
        if let Some(key) = &idempotency_key {
            if let Some(existing) = self.find_by_idem(key).await? {
                return Ok(PagoCreatedResp {
                    payment_id: existing._id,
                    status: existing.status,
                });
            }
        }

        let pago = Pago::new(
            dto.trip_id,
            user_id,
            dto.amount,
            dto.currency,
            dto.method,
            idempotency_key.clone(),
        );
        let doc = to_document(&pago).map_err(|_| actix_web::error::ErrorInternalServerError("serialize error"))?;
        self.collection.insert_one(doc, None).await
            .map_err(|e| {
                if e.to_string().contains("E11000") {
                    actix_web::error::ErrorConflict("Idempotency-Key duplicada")
                } else {
                    actix_web::error::ErrorInternalServerError("Mongo insert error")
                }
            })?;

        Ok(PagoCreatedResp { payment_id: pago._id, status: pago.status })
    }

    pub async fn detalle(&self, id: &str) -> Result<Option<PagoDetailResp>, actix_web::Error> {
        let q = doc! { "_id": id };
        if let Some(doc) = self.collection.find_one(q, None).await.map_err(|_| actix_web::error::ErrorInternalServerError("Mongo find error"))? {
            let pago: crate::models::pago::Pago = mongodb::bson::from_document(doc)
                .map_err(|_| actix_web::error::ErrorInternalServerError("deserialize error"))?;
            return Ok(Some(PagoDetailResp { payment: pago }));
        }
        Ok(None)
    }

    pub async fn find_by_trip(&self, trip_id: &str) -> Result<Vec<Pago>, actix_web::Error> {
        let q = doc! { "trip_id": trip_id };
        let mut cur = self.collection.find(q, None).await
            .map_err(|_| actix_web::error::ErrorInternalServerError("Mongo find error"))?;
        let mut out = vec![];
        while let Some(doc) = cur.try_next().await
            .map_err(|_| actix_web::error::ErrorInternalServerError("cursor error"))? {
            let pago: Pago = mongodb::bson::from_document(doc)
                .map_err(|_| actix_web::error::ErrorInternalServerError("deserialize error"))?;
            out.push(pago);
        }
        Ok(out)
    }

    async fn find_by_idem(&self, idem: &str) -> Result<Option<Pago>, actix_web::Error> {
        let q = doc! { "idempotency_key": idem };
        if let Some(doc) = self.collection.find_one(q, None).await
            .map_err(|_| actix_web::error::ErrorInternalServerError("Mongo find error"))? {
            let pago: Pago = mongodb::bson::from_document(doc)
                .map_err(|_| actix_web::error::ErrorInternalServerError("deserialize error"))?;
            Ok(Some(pago))
        } else {
            Ok(None)
        }
    }
}
