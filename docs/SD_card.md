# SD卡根目录结构

SD卡根目录中包括以下内容：

| 文件 | 作用 |
| ---- | ---- |
| indexXX.bin | 记录文件目录 |
| hivXXXXX.mp4 | 记录文件 |
| log.bin | 运行日志 |
| MiniPlayer文件夹 | 自带播放器 |
| HIKWS | 不明 |

### indexXX.bin文件

主要包括`index00.bin` `index01.bin` `index02.bin`这三个文件。他们的结构完全相同，是记录文件的目录，用来记录视频的起止时间、抓拍拍照时间、文件长度等信息。

详见[indexXX.bin 文件结构](./index.md)。

### hivXXXXX.mp4文件

`hivXXXXX.mp4`中的`XXXXX`代表5位数字。这些是行车记录仪的记录文件，结构较为复杂。记录了包括录音录像、紧急抓拍、GPS、加速度计、绿灯识别等信息。

详见[hivXXXXX.mp4 文件简介](./hiv_mp4.md)。

### log.bin文件

这个文件记录了日志信息，如开关机，时间调整，进入、退出停车监控模式等。

详见[log.bin 文件结构](./log.md)。

### MiniPlayer文件夹

这个文件夹包含自带播放器，可以用来播放以及导出记录视频文件、抓拍照片等。

### HIKWS文件

用途未知
