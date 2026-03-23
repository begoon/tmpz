import Foundation

let activity = ProcessInfo.processInfo.beginActivity(
    options: [.idleSystemSleepDisabled, .idleDisplaySleepDisabled],
    reason: "Keep Mac awake"
)

print("Sleep prevention is ON. Press Ctrl+C to stop.")

RunLoop.main.run()

