use mongodb::{options::ClientOptions, Client, Database, IndexModel, bson::doc};

#[derive(Clone)]
pub struct DbState {
    pub db: Database,
}

impl DbState {
    pub async fn connect(uri: &str, db_name: &str) -> mongodb::error::Result<Self> {
        let mut opts = ClientOptions::parse(uri).await?;
        opts.app_name = Some("servicio-pagos".into());
        let client = Client::with_options(opts)?;
        let db = client.database(db_name);

        // índices útiles
        let pagos = db.collection::<mongodb::bson::Document>("pagos");
        let _ = pagos.create_index(IndexModel::builder().keys(doc!{"trip_id":1}).build(), None).await;
        let _ = pagos.create_index(IndexModel::builder().keys(doc!{"idempotency_key":1}).options(
            mongodb::options::IndexOptions::builder().unique(true).build()
        ).build(), None).await;

        Ok(Self { db })
    }
}
