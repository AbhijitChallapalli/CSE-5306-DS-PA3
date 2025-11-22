// microservice_based/alarm_dist_sys/scheduler/scheduler_decision.js

const grpc = require("@grpc/grpc-js");
const protoLoader = require("@grpc/proto-loader");

const NODE_ID = "scheduler";
const PHASE_DECISION = "Decision";

// Load proto
const packageDefinition = protoLoader.loadSync("alarm.proto", {
  keepCase: true,
  longs: String,
  // DO NOT set enums:String here; we want numeric enums by default.
  defaults: true,
  oneofs: true,
});

const alarmProto = grpc.loadPackageDefinition(packageDefinition).alarm;

const preparedAlarms = {}; // tx_id -> Alarm

function AddPreparedAlarm(call, callback) {
  const txIdStr = call.request.tx_id.id;
  const alarm = call.request.alarm;

  console.log(
    `Phase ${PHASE_DECISION} of Node ${NODE_ID} ` +
      `sends RPC AddPreparedAlarm to Phase ${PHASE_DECISION} of Node ${NODE_ID}`
  );

  preparedAlarms[txIdStr] = alarm;

  callback(null, {
    tx_id: call.request.tx_id,
    success: true,
    message: "Prepared alarm stored on scheduler",
  });
}

function DecideOnAddAlarm(call, callback) {
  const txIdStr = call.request.tx_id.id;
  const decision = call.request.decision;

  console.log(
    `Phase ${PHASE_DECISION} of Node ${NODE_ID} ` +
      `sends RPC DecideOnAddAlarm to Phase ${PHASE_DECISION} of Node ${NODE_ID}`
  );
//   console.log(
//     `[Scheduler DecisionPhase] Raw decision value from wire:`,
//     decision,
//     "typeof:",
//     typeof decision
//   );

  if (!preparedAlarms[txIdStr]) {
    callback(null, {
      tx_id: call.request.tx_id,
      success: false,
      message: "No prepared alarm on scheduler for this tx_id",
    });
    return;
  }

  const alarm = preparedAlarms[txIdStr];
  delete preparedAlarms[txIdStr];

  // Robust check: handle numeric and string enums
  const isGlobalCommit =
    decision === alarmProto.GlobalDecision.GLOBAL_COMMIT ||
    decision === "GLOBAL_COMMIT" ||
    decision === 0;

  if (isGlobalCommit) {
    // ----- COMMIT PATH -----
    const schedClient = new alarmProto.Scheduler(
      "localhost:50052",
      grpc.credentials.createInsecure()
    );

    console.log(
      `[Scheduler DecisionPhase] COMMIT: calling Scheduler.ScheduleAlarm for tx_id=${txIdStr}`
    );

    schedClient.ScheduleAlarm(alarm, (err, _resp) => {
      if (err) {
        console.error("Scheduler.ScheduleAlarm error:", err);
        callback(null, {
          tx_id: call.request.tx_id,
          success: false,
          message: "Scheduler commit failed: " + err.message,
        });
      } else {
        callback(null, {
          tx_id: call.request.tx_id,
          success: true,
          message: "Scheduler committed alarm",
        });
      }
    });
  } else {
    // ----- ABORT PATH -----
    console.log(
      `[Scheduler DecisionPhase] ABORT: dropping prepared alarm for tx_id=${txIdStr}`
    );
    callback(null, {
      tx_id: call.request.tx_id,
      success: true,
      message: "Scheduler aborted alarm (global abort)",
    });
  }
}

function main() {
  const server = new grpc.Server();
  server.addService(alarmProto.DecisionPhase.service, {
    AddPreparedAlarm,
    DecideOnAddAlarm,
  });

  server.bindAsync(
    "0.0.0.0:61052",
    grpc.ServerCredentials.createInsecure(),
    () => {
      console.log(
        "Scheduler DecisionPhase (Node.js) listening on port 61052"
      );
      server.start();
    }
  );
}

main();
