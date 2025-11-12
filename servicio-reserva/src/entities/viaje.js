const { EntitySchema } = require("typeorm");

module.exports = new EntitySchema({
  name: "Viaje",
  tableName: "viajes",
  columns: {
    id_viaje: {
      type: Number,
      primary: true,
      generated: true
    },
    id_cliente: {
      type: Number,
      nullable: false
    },
    id_conductor: {
      type: Number,
      nullable: false
    },
    punto_origen: {
      type: String,
      nullable: false
    },
    punto_destino: {
      type: String,
      nullable: false
    },
    estado: {
      type: String,
      default: "pendiente" // pendiente, asignado, en_progreso, finalizado, cancelado
    },
    fecha_solicitud: {
      type: "datetime",
      createDate: true
    },
    fecha_inicio: {
      type: "datetime",
      nullable: true
    },
    fecha_fin: {
      type: "datetime",
      nullable: true
    }
  }
});
