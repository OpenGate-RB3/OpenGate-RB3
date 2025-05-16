import time
import os
import requests
from periphery import GPIO

# --- Configuration ---
GPIO_CHIP_DEVICE_ENV = os.environ.get("GPIO_CHIP_DEVICE", "/dev/gpiochip4")
GPIO_LINE_OFFSET_ENV = int(os.environ.get("GPIO_LINE_OFFSET", "36"))

NTFY_TOPIC = "open_gate_notif"
NTFY_MESSAGE = "Button pressed 😀"
NO_HIGH_TIMEOUT = 2.0  # Seconds without detecting HIGH to consider button pressed

print(f"--- GPIO Monitor - 'No HIGH for {NO_HIGH_TIMEOUT}s' Logic (in Docker) ---")
print(f"Using Chip: {GPIO_CHIP_DEVICE_ENV}, Line: {GPIO_LINE_OFFSET_ENV}")
print(f"Notification will be sent to: https://ntfy.sh/{NTFY_TOPIC}")
print(
    f"If HIGH not detected for {NO_HIGH_TIMEOUT} seconds, a notification will be sent."
)
print("Press Ctrl+C to exit.")

gpio_in = None
# Initialize last_high_seen_time to current time, assumes pin might initially be high or just became active.
# This prevents an immediate notification on startup if the pin starts low.
last_high_seen_time = time.monotonic()
notification_sent_this_cycle = False

try:
    gpio_in = GPIO(GPIO_CHIP_DEVICE_ENV, GPIO_LINE_OFFSET_ENV, "in")
    initial_state_is_high = gpio_in.read()
    print(
        f"Successfully opened {GPIO_CHIP_DEVICE_ENV} line {GPIO_LINE_OFFSET_ENV}. Initial raw state: {'HIGH' if initial_state_is_high else 'LOW'}"
    )
    if initial_state_is_high:
        last_high_seen_time = time.monotonic()  # Correctly update if it starts HIGH
    else:
        # If it starts LOW, we consider the "no high" period to have just begun from script start for safety,
        # or more accurately, from a slightly deferred point to allow initial stabilization if needed.
        # Setting it to current time is safe, it means 2s from now if it stays low.
        last_high_seen_time = time.monotonic()

    while True:
        current_pin_is_high = gpio_in.read()  # True for HIGH, False for LOW
        current_time = time.monotonic()

        if current_pin_is_high:
            last_high_seen_time = current_time
            if notification_sent_this_cycle:
                print("Pin went HIGH, re-arming notification.")
                notification_sent_this_cycle = False
        else:  # Pin is currently LOW
            if not notification_sent_this_cycle:
                time_since_last_high = current_time - last_high_seen_time
                if time_since_last_high >= NO_HIGH_TIMEOUT:
                    print(
                        f"No HIGH signal for {time_since_last_high:.2f}s. Sending notification to ntfy.sh/{NTFY_TOPIC}..."
                    )
                    try:
                        response = requests.post(
                            f"https://ntfy.sh/{NTFY_TOPIC}",
                            data=NTFY_MESSAGE.encode(encoding="utf-8"),
                            headers={"Title": "Gate Button Alert"},
                        )
                        if response.status_code == 200:
                            print("Notification sent successfully.")
                        else:
                            print(
                                f"Failed to send ntfy. Status: {response.status_code}, Resp: {response.text}"
                            )
                    except requests.exceptions.RequestException as e:
                        print(f"Error sending ntfy notification: {e}")
                    notification_sent_this_cycle = (
                        True  # Set flag to prevent re-sending
                    )

        time.sleep(0.1)  # Poll every 100ms

except (GPIOError, IOError, FileNotFoundError) as e:
    print(f"\nError opening/reading GPIO: {e}")
except KeyboardInterrupt:
    print("\nExiting script...")
finally:
    if gpio_in:
        gpio_in.close()
        print("\nGPIO closed.")
