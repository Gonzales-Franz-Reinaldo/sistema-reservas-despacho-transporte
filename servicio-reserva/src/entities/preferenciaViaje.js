const { EntitySchema } = require("typeorm");

module.exports = new EntitySchema({
  name: "PreferenciaViaje",
  tableName: "preferencias_viaje",
  columns: {
    id_preferencia: {
      type: Number,
      primary: true,
      generated: true
    },
    id_cliente: {
      type: Number,
      nullable: false
    },
    tipo_vehiculo: {
      type: String,
      nullable: true
    },
    metodo_pago_preferido: {
      type: String,
      nullable: true
    }
  }
});
