docker build -t rb3-gpio-monitor .

docker run --rm -it \
 --device=/dev/gpiochip0 \
 --device=/dev/gpiochip1 \
 --device=/dev/gpiochip2 \
 --device=/dev/gpiochip3 \
 --device=/dev/gpiochip4 \
 --device=/dev/gpiochip5 \
 -e GPIO_CHIP_DEVICE="/dev/gpiochip4" \
 -e GPIO_LINE_OFFSET="36" \
 --network host \
 rb3-gpio-monitor
