cmake_minimum_required(VERSION 3.12)
include(pico_sdk_import.cmake)
project(Pico_ePaper_Code)
pico_sdk_init()

#添加编译子目录
add_subdirectory(lib/Config)
add_subdirectory(lib/Infrared)
add_subdirectory(lib/HTTP)
add_subdirectory(lib/MQTT)
add_subdirectory(lib/AT)
add_subdirectory(lib/GPS)
add_subdirectory(examples)



#添加头文件目录
include_directories(examples)
include_directories(./lib/Config)
include_directories(./lib/Infrared)
include_directories(./lib/HTTP)
include_directories(./lib/MQTT)
include_directories(./lib/AT)
include_directories(./lib/GPS)
# 生成可执行文件
add_executable(main 
main.c
)

# enable usb output, disable uart output
pico_enable_stdio_usb(main 1)
pico_enable_stdio_uart(main 0)

# create map/bin/hex/uf2 file etc.
pico_add_extra_outputs(main)

target_link_libraries(main examples Infrared Config HTTP MQTT AT pico_stdlib)

