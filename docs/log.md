# log.bin 文件结构

`log.bin`文件是一个日志，内容为行车记录仪首次运行以来的各种日志信息。日志内容包括了开机，掉电（关机），时间调整，进入、退出停车监控模式等。

日志文件主要包括了一个header和之后的若干条log。主要结构如下：

| 偏移量 | 字节数 | 包含信息 |
| ---- | ---- | ---- |
| 0x0000 | 0x2000 | header，说明后面log的数量 |
| 0x2000 | 0x90 | log |
| 0x2090 | 0x90 | log |
| 0x2120 | 0x90 | log |
| ... | ... | ... |

首先是一个`0x2000`长度的header，header中记录后面log的数量。之后从偏移量`0x2000`开始，每`0x90`为1条log，直到文件末尾。

`log.bin`文件的长度固定为`0x480040`，去掉`0x2000`的header后用于log的大小有`0x47E040`字节。但是，`0x47E040 = 0x90 * 0x7FC7 + 0x50`，因此这个长度并不是单条log长`0x90`的整数倍。可能log文件结尾部分处的内容还有其他含义。

## header

header长为`0x2000`，除了开头`0x12`以外全为`0x00`。其结构如下：

| 偏移量 | 字节数 | 类型 | 猜测含义 |
| ---- | ---- | ---- | ---- |
| 0x00 | 4 | char[] | 总是`SWKH` |
| 0x04 | 12 | NA | 不明 |
| 0x10 | 2 | uint16 | log数量，记为`log_num` |
| 0x12 | 0x1FEE | NA | 不明，总是`0x00` |

## log

log区固定开始于`0x2000`，每条长度`0x90`，条目数量为`log_num`。每条log的格式如下：

| 偏移量 | 字节数 | 类型 | 猜测含义 |
| ---- | ---- | ---- | ---- |
| 0x00 | 4 | uint32 | 时间戳，log的产生时间 |
| 0x04 | 4 | NA | 不明，可能与日志类型有关</br>记为`type_id` |
| 0x08 | 4 | NA | 不明，总是`0x00` |
| 0x0C | 132 | char[]<sup>1</sup> | log字符串 |

<sup>1</sup> 通常是字符串格式，个别日志中也会出现二进制数据。

下面介绍几种常见的log内容及其对应的`type_id`

### 开机log

`type_id = 0x01 0x00 0x10 0x00`

连接电源后产生。如果连接的是带有数据线的USB线（包括原厂保险盒降压线），log内容为：

`power:protection line`

否则，如果USB线没有数据线，则log内容为：

`power:normal line`

USB线没有数据线时，无法进入停车监控模式。

### 掉电

`type_id = 0x01 0x00 0x0C 0x00`

拔下电源线之前产生。log内容：

`Low power[value]`

其中，怀疑`value`是内部ADC采样的分压之后的电压值。观察到所有`value`都略小于1300。

### 进入/退出停车监控

进入停车监控时产生的log：

`PARKING ENTER`

退出停车监控时产生的log：

`PARKING EXIT`

### 版本及序列号log

`type_id = 0x01 0x00 0x01 0x00`

每次开机log之后，会产生一条记录固件版本以及行车记录仪序列号的log。版本用二进制格式记录，序列号用ascii字符串记录。

假定固件版本号格式为`X.Y.Z`，log格式为：

| 偏移量 | 字节数 | 类型 | 猜测含义 |
| ---- | ---- | ---- | ---- |
| 0x00 | 2 | uint16 | 固件版本号`Z` |
| 0x02 | 1 | uint8 | 固件版本号`Y` |
| 0x03 | 1 | uint8 | 固件版本号`X` |
| 0x04 | 2 | uint16 | 固件日期中的年 |
| 0x06 | 1 | uint8 | 固件日期中的月 |
| 0x07 | 1 | uint8 | 固件日期中的日 |
| 0x08 | 12 | NA | 不明 |
| 0x14 | 112 | char[] | 序列号 |

### <span id="jump_modify_timezone">修改时区</span>

`type_id = 0x03 0x00 0x09 0x00`

内部时区发生变化时产生。log内容：

`GMTHH:MM to GMTHH:MM`

左边的`HH`和`MM`是变化前时区，右边的是变化后时区。在西半球，`HH`可能有一个额外的负号。

### 设定时区

`type_id = 0x03 0x00 0x09 0x00`

内部时区被**设定**时产生。每次连接APP都会设定时区，但是设定后时区不一定发生变化。只有发生变化后才会产生[修改时区log](#jump_modify_timezone)。

log内容：

`TimeZone YYYY-MM-DD HH:MM:SS to YYYY-MM-DD HH:MM:SS\n`

左边是设定前的时间，右边是设定后的时间。

### GPS同步时间

`type_id = 0x03 0x00 0x09 0x00`

每次通过GPS同步内部时钟后产生。开机后，如果之前有几天没有同步过了，才会同步。log内容：

`GPS YYYY-MM-DD HH:MM:SS to YYYY-MM-DD HH:MM:SS\n`

### 修改WiFi密码

`type_id = 0x03 0x00 0x09 0x00`

通过APP修改WiFi密码后产生。log内容：

`Wifi ap passwd set.`

### 其他log

修改过行车记录仪的设置之后，也可能会产生某些log。由于不常见，此处不做说明。

</br></br>
返回[SD卡根目录结构](./SD_card.md)