#!/usr/bin/env bash

call_cat="adb shell cat" # cat命令
call_ls="adb shell ls" # ls命令
name_base="/dev/block/bootdevice" # by-name的上级目录，一般不用动
if [[ -n $1 ]]; then
  block_name=$(${call_ls} -la ${name_base}/by-name/$1 2>/dev/null | awk -F " -> /dev/block/" '{print $2}') # 将 分区可读名称 转换为 块设备名称
  if [[ -n ${block_name} ]]; then
    ${call_cat} /proc/partitions | grep ${block_name} | awk -F " " '{print $3 * 1024}' # 输出单位为 Byte
  else
    echo "Error: partition $1 not found"
  fi
else
  echo "Usage: $0 [partition name]"
fi
