// microservice_based/alarm_dist_sys/accounts/accounts_decision.js

const grpc = require("@grpc/grpc-js");
const protoLoader = require("@grpc/proto-loader");

const NODE_ID = "accounts";
const PHASE_DECISION = "Decision";

// Load proto
const packageDefinition = protoLoader.loadSync("alarm.proto", {
  keepCase: true,
  longs: String,
  // DO NOT set enums:String here
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
    message: "Prepared alarm stored on accounts",
  });
}

function DecideOnAddAlarm(call, callback) {
  const txIdStr = call.request.tx_id.id;
  const decision = call.request.decision;

  console.log(
    `Phase ${PHASE_DECISION} of Node ${NODE_ID} ` +
      `sends RPC DecideOnAddAlarm to Phase ${PHASE_DECISION} of Node ${NODE_ID}`
  );
  // console.log(
  //   `[Accounts DecisionPhase] Raw decision value from wire:`,
  //   decision,
  //   "typeof:",
  //   typeof decision
  // );

  if (!preparedAlarms[txIdStr]) {
    callback(null, {
      tx_id: call.request.tx_id,
      success: false,
      message: "No prepared alarm on accounts for this tx_id",
    });
    return;
  }

  const alarm = preparedAlarms[txIdStr];
  delete preparedAlarms[txIdStr];

  const isGlobalCommit =
    decision === alarmProto.GlobalDecision.GLOBAL_COMMIT ||
    decision === "GLOBAL_COMMIT" ||
    decision === 0;

  if (isGlobalCommit) {
    console.log(
      `[Accounts DecisionPhase] COMMIT: logically committing alarm for tx_id=${txIdStr}`
    );
    callback(null, {
      tx_id: call.request.tx_id,
      success: true,
      message: "Accounts committed alarm",
    });
  } else {
    console.log(
      `[Accounts DecisionPhase] ABORT: logically aborting alarm for tx_id=${txIdStr}`
    );
    callback(null, {
      tx_id: call.request.tx_id,
      success: true,
      message: "Accounts logically aborted alarm (global abort)",
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
    "0.0.0.0:61053",
    grpc.ServerCredentials.createInsecure(),
    () => {
      console.log(
        "Accounts DecisionPhase (Node.js) listening on port 61053"
      );
      server.start();
    }
  );
}

main();
