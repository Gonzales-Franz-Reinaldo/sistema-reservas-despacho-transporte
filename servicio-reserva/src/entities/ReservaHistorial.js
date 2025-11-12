const { EntitySchema } = require("typeorm");

module.exports = new EntitySchema({
  name: "ReservaHistorial",
  tableName: "reservas_historial",
  columns: {
    id_historial: {
      type: Number,
      primary: true,
      generated: true
    },
    accion: {
      type: String,
      nullable: false
    },
    fecha_accion: {
      type: "datetime",
      createDate: true
    },
    detalle: {
      type: String,
      nullable: true
    }
  },
  relations: {
    viaje: {
      type: "many-to-one",
      target: "Viaje",
      joinColumn: { name: "id_viaje" },
      onDelete: "CASCADE"
    }
  }
});
