# 视频文件分段结构

如[记录文件总体结构](./hiv_mp4.md#jump_mp4_general)所述，每个记录文件都包括一个或多个完全相同的分段。每一分段存储一段视频。`hivXXXXX.mp4`文件的总体结构应为：

| `hivXXXXX.mp4`文件 |
| :----: |
| 第1段 |
| 第2段 |
| ... |

本文讨论具体某一个分段内的结构。

对于视频文件，每个分段的5节所包含内容如下：

| 节数 | 相对分段开始位置 | 长度 | 主要内容 |
| ---- | ---- | ---- |---- |
| 1 | 0x00000 | 0x10000 | GPS记录 |
| 2 | 0x10000 | 0x10000 | 紧急录像数据 |
| 3 | 0x20000 | 0x1E000 | 视频缩略图 |
| 4 | 0x3E000 | 0x02000 | 不明 |
| 5 | 0x40000 | 到本个分段结尾 | 视频、音频、</br>GPS记录、加速度计记录、</br>红绿灯识别、前车起步识别 |

### 关于位置的说明

每个分段的开始位置可以从`indexXX.bin`目录文件中[找到](./index.md#jump_s4_video)。但要注意，目录文件中记录的是音视频数据开始的位置（也即第5节开始的位置）。若要得到分段的开始位置，需要将目录文件中记录的每一分段开始位置**减**去`0x40000`。

每个分段的结束位置也可以在`indexXX.bin`目录文件中[找到](./index.md#jump_s4_video)。目录文件中的这一项在这里无需调整，可直接使用。

**为简化说明，后文中出现的“位置”都默认是从分段开始处计算的位置，而非从文件开始处计算。**

## 第1节

本节开始位置固定为`0x0`，观察知其长度为`0x10000`。

本节包括一个不符合标准的 private_stream_2 PES packet，主要包含每秒视频在视频数据中的偏移量以及对应的GPS轨迹信息。

本节总体结构：

|  | 节内偏移量 | 字节数 | 内容 |
| ---- | ---- | ---- | ---- |
| header | 0x00 | 0x20 | 包括本分段视频总体信息 |
| body | 0x20 | 0x30 | 第1秒视频及GPS信息 |
|  | 0x50 | 0x30 | 第2秒视频及GPS信息 |
|  | 0x80 | 0x30 | 第3秒视频及GPS信息 |
|  | ... | 0x30 | ... |

### header

本节内`0x0 - 0x1F`的内容似乎是一个header。

| 偏移量 | 字节数 | 类型 | 猜测含义 |
| ---- | ---- | ---- | ---- |
| 0x00 | 3 | NA | packet_start_code_prefix，总是`0x00 0x00 0x01` |
| 0x01 | 1 | NA | stream_id，总是`0xBF`，表示private_stream_2 |
| 0x04 | 2 | uint16 | PES_packet_length，大端序，总是`0xFF8F`<sup>1</sup> |
| 0x06 | 2 | NA | 不明，总是`0xF8 0xFF` |
| 0x08 | 4 | NA | 不明，总是`0x00` |
| 0x0C | 4 | uint32 | 本分段音视频数据长度<sup>2</sup> |
| 0x10 | 1 | NA | 不明，总是`0x01` |
| 0x11 | 1 | NA | 不明</br>0x00：正常录像</br>0x63：停车监控 |
| 0x12 | 1 | uint8 | 录像帧率（fps）：</br>30：正常录像<sup>3</sup></br>1：停车监控 |
| 0x13 | 1 | NA | 不明</br>0x13：正常录像</br>0x00：停车监控 |
| 0x14 | 4 | uint32 | 时间戳，本分段结束时间 |
| 0x18 | 4 | NA | 不明，总是`0x00` |
| 0x1C | 2 | uint16 | 后续GPS数据体长度<sup>4</sup> |
| 0x1E | 1 | NA | 不明，总是`0x01` |
| 0x1F | 1 | NA | 不明，可能是某种校验和 |

<sup>1</sup> PES_packet_length仍属于MPEG-PS标准，用大端序表示；后续内容属于自定义数据，观察发现是小端序。根据标准，这个PES packet的长度不应是`0xFF8F`，而应是`0x10000 - 0x6 = 0xFFFA`。因此说本节是一个不符合标准的PES_packet。

<sup>2</sup> 这里指的是第5段（音视频数据）的长度，不算前面4段总计`0x4000`的额外信息。

<sup>3</sup> 正常录像的帧率随设置而改变。

<sup>4</sup> 后续数据指的是后边以`0x30`为一组的GPS数据长度。因此这里除以`0x30`可以知道后面记录GPS数据点的个数。

### body

接下来的数据以`0x30`为一组，代表了某一秒钟的视频与GPS信息。

GPS信息使用的是WGS84坐标系，其与国内使用的GCJ02坐标系有一定的偏差。如果想要把行车轨迹显示在地图上，需要注意地图所使用的坐标系是否同为WGS84，否则需要转换坐标系。谷歌地图和OpenStreetMap都使用WGS84坐标系，不需要坐标系转换。

对每条长`0x30`的数据，结构如下：

| 偏移量 | 字节数 | 类型 | 猜测含义 |
| ---- | ---- | ---- | ---- |
| 0x00 | 2 | NA | 不明，总是`0x78 0x56` |
| 0x02 | 2 | NA | 不明，对于视频文件，总是`0x01 0x00` |
| 0x04 | 4 | uint32 | 时间戳，开始时间 |
| 0x08 | 4 | uint32 | 时间戳处视频相对于音视频数据开始位置<sup>1</sup>的偏移量 |
| 0x0C | 4 | uint32 | 相对于上一行所述的位置，到下一个private_stream_1或pack_header的偏移量 |
| 0x10 | 4 | uint32 | 无符号经度，以百分之一***秒***为单位 |
| 0x14 | 4 | uint32 | 无符号纬度，以百分之一***秒***为单位 |
| 0x18 | 4 | uint32 | 车速，以千米每小时为单位 |
| 0x1C | 4 | uint32 | 速度方位角<sup>2</sup>，以百分之一***度***为单位 |
| 0x20 | 4 | uint32 | 高度<sup>3</sup>，以厘米为单位 |
| 0x24 | 1 | uint8 | 是否定位有效：</br>1：定位有效</br>0：定位无效 |
| 0x25 | 1 | char | 东经或西经：</br>`E`：东经</br>`W`：西经 |
| 0x26 | 1 | char | 北纬或南纬：</br>`N`：北纬</br>`S`：南纬 |
| 0x27 | 1 | NA | 不明，总是`0x00` |
| 0x28 | 8 | NA | 不明，总是`0x00` |

<sup>1</sup> “视频数据开始位置”指的是本分段中第5节的开始位置，即本分段开始位置之后的`0x40000`。

<sup>2</sup> 从天上向下看，从正北顺时针旋转的角度。

<sup>3</sup> 此处的高度指的是距离[GPS参考椭球面](https://zh.wikipedia.org/wiki/%E5%8F%82%E8%80%83%E6%A4%AD%E7%90%83)的椭球高，而非距离[大地水准面](https://zh.wikipedia.org/wiki/%E5%A4%A7%E5%9C%B0%E6%B0%B4%E5%87%86%E9%9D%A2)的正高。因此可能出现在海边但高度不为0的情况。

无法定位时，经纬度、速度、方位角高度等信息不存在。因此`0x10`及处以后的数据都为`0x00`。

后续至第2节开始前数据都为`0x00`。

## 第2节

本节开始位置固定为`0x10000`，观察知其长度为`0x10000`。

本节包括一个不符合标准的 private_stream_2 PES packet。如果某一视频分段包含了紧急录像，则此处记录了分段内紧急录像的信息。

本节总体结构：

|  | 节内偏移量 | 字节数 | 内容 |
| ---- | ---- | ---- | ---- |
| header | 0x00 | 0x20 | 后续内容长度 |
| body | 0x20 | 0x10 | 分段内第1段紧急录像信息 |
|  | 0x30 | 0x10 | 分段内第2段紧急录像信息 |
|  | ... | 0x10 | ... |

### header

本节内`0x0 - 0x1F`的内容似乎是一个header。

| 偏移量 | 字节数 | 类型 | 猜测含义 |
| ---- | ---- | ---- | ---- |
| 0x00 | 3 | NA | packet_start_code_prefix，总是`0x00 0x00 0x01` |
| 0x01 | 1 | NA | stream_id，总是`0xBF`，表示private_stream_2 |
| 0x04 | 2 | uint16 | PES_packet_length，大端序，总是`0xFF8F`<sup>1</sup> |
| 0x06 | 2 | NA | 不明，总是`0xF8 0x7F` |
| 0x08 | 20 | NA | 不明，总是`0x00` |
| 0x1C | 2 | uint16 | 后续数据体长度<sup>2</sup> |
| 0x1E | 1 | NA | 不明，总是`0x02` |
| 0x1F | 1 | NA | 不明，可能是某种校验和 |

<sup>1</sup> 同第1节，此处长度不正确，因此第2节包含的PES包也不符合标准。

<sup>2</sup> 后续每条数据长度为`0x10`，因此可根据长度确定后续数据条数。

如果某一分段视频里面没有紧急录像，则此处的长度应为`0x00`，后面数据体里面也全为`0x00`。

### body

当存在紧急录像时，接下来每条数据长`0x10`，代表了一段紧急录像的信息。

对每条长`0x10`的数据：

| 偏移量 | 字节数 | 类型 | 猜测含义 |
| ---- | ---- | ---- | ---- |
| 0x00 | 2 | NA | 不明，总是`0x78 0x56` |
| 0x02 | 2 | NA | 不明，总是`0x02 0x00` |
| 0x04 | 4 | uint32 | 时间戳，紧急录像触发时间 |
| 0x08 | 2 | NA | 总是`0x06 0x00` |
| 0x0A | 2 | NA | 总是`0x06 0x00` |
| 0x0C | 4 | NA | 总是`0x00` |

后续至第3节开始前数据都为`0x00`。

## 第3节

本节开始位置固定为`0x20000`，观察知其长度为`0x1E000`。

本节包括一个不符合标准的 private_stream_2 PES packet，其中包含了一张视频开始时画面的缩略图。

本节总体结构：

|  | 节内偏移量 | 字节数 | 内容 |
| ---- | ---- | ---- | ---- |
| header | 0x00 | 0x20 | 缩略图大小 |
| body | 0x20 | 可变 | 缩略图 |

### header

本节内`0x0 - 0x1F`的内容似乎是一个header。

| 偏移量 | 字节数 | 类型 | 猜测含义 |
| ---- | ---- | ---- | ---- |
| 0x00 | 3 | NA | packet_start_code_prefix，总是`0x00 0x00 0x01` |
| 0x01 | 1 | NA | stream_id，总是`0xBF`，表示private_stream_2 |
| 0x04 | 2 | uint16 | PES_packet_length，大端序，总是`0xFF8F`<sup>1</sup> |
| 0x06 | 2 | NA | 不明，总是`0xF8 0xFF` |
| 0x08 | 20 | NA | 不明，总是`0x00` |
| 0x1C | 2 | uint16 | 后续缩略图长度 |
| 0x1E | 1 | NA | 不明，总是`0x04` |
| 0x1F | 1 | NA | 不明，可能是某种校验和，总是`0x45` |

<sup>1</sup> 同第1节，此处长度不正确，因此第3节包含的PES包也不符合标准。

### body

观察body中二进制数据，发现以`0xFF 0xD8`开头，以`0xFF 0xD9`结尾，长度为header中记录的长度。因此可知body中包含一张JPEG格式图片。

解码显示后发现是视频开始处画面的缩略图。

后续至第4节开始前数据都为`0x00`。

## 第4节

本节开始位置固定为`0x3E0000`，观察知其长度为`0x2000`。

本节包括一个不符合标准的 private_stream_2 PES packet，含义不明。

本节总体结构：

|  | 节内偏移量 | 字节数 | 内容 |
| ---- | ---- | ---- | ---- |
| header | 0x00 | 0x20 | 不明 |

### header

本节内容似乎只包含`0x0 - 0x1F`处的header。

| 偏移量 | 字节数 | 类型 | 猜测含义 |
| ---- | ---- | ---- | ---- |
| 0x00 | 3 | NA | packet_start_code_prefix，总是`0x00 0x00 0x01` |
| 0x01 | 1 | NA | stream_id，总是`0xBF`，表示private_stream_2 |
| 0x04 | 2 | uint16 | PES_packet_length，大端序，总是`0xFF8F`<sup>1</sup> |
| 0x06 | 2 | NA | 不明，总是`0xF8 0x1F` |
| 0x08 | 22 | NA | 不明，总是`0x00` |
| 0x1E | 1 | NA | 不明，总是`0x07` |
| 0x1F | 1 | NA | 不明，可能是某种校验和，总是`0x65` |

<sup>1</sup> 同第1节，此处长度不正确，因此第3节包含的PES包也不符合标准。

后续至第5节开始前数据都为`0x00`。

## 第5节

本节开始位置固定为`0x400000`，内容为视频、录音、GPS、加速度计、红绿灯识别、前车起步识别等信息。其长度可变，由[第1节](#第1节)的header内信息确定。

### 总体结构

本节完全符合MPEG - Program Stream格式标准。Program Stream由一系列的Program Stream pack header和PES packet组成。根据ISO/IEC 13818-1 §2.5.3.3，Program Stream结构如下表：

| pack | 内容 |
| ---- | ---- |
| pack 1 | pack_header |
|  | PES_packet 1 |
|  | PES_packet 2 |
|  | ... |
| pack 2 | pack_header |
|  | PES_packet 1 |
|  | PES_packet 2 |
|  | ... |
| ... | ... |

再观察PES_packet，可发现数据中出现的PES_packet分为以下几类：

| stream_id | 类型 | 内容 |
| ---- | ---- | ---- |
| 0xBC | program_stream_map | 节目流映射相关，见ISO/IEC 13818-1 §2.5.4 |
| 0xE0 | video | 视频，HEVC编码 |
| 0xC0 | audio | 音频，AAC LC编码，采样率16kHz，单声道 |
| 0xBD | private_stream_1 | GPS、加速度计、红绿灯识别、前车起步识别等 |

### 一些观察

通过观察，发现整个Program Stream中pack的数量与视频的总帧数相等。每个pack内都会包括数个视频数据包，因此推测每个pack包括一帧视频的数据。

对于音频，每几个pack中会出现一个音频数据包。可能是音频数据量不大，因此不用每一帧都记录一次音频数据。

对于program_stream_map，观察发现每秒钟第一帧的pack_header后会出现program_stream_map。

最后是private_stream_1数据包，其包括内容很多，且data为自定义格式。不同种类的数据出现频率不同。

### program_stream_map video audio包

对于program_stream_map、视频和音频的PES_packet结构，请参阅相关公开的标准文件，后续仅讨论行车记录仪自定义的private_stream_1的结构。

### PES_packet结构

根据标准，所有PES_packet都包括header和后面的data两部分。如下表：

|  | 内容 |
| ---- | ---- |
| header | 包类型、包长度、config信息、时间戳等 |
| data | 具体数据 |

下面说明private_stream_1 PES_packet的header和data结构。

### <span id="jump_pes_header">private_stream_1 PES_packet header</span>

PES_packet header长度会因其config不同而不同。但是根据观察，文件中所有的private_stream_1 packet的config均相同，因此所有header的格式都一样，长度都为`0x10`。header结构如下表。***header中基本只有PES_packet_length对后续分析有用。***

| Syntax | *比特*数 | 注释 |
| ---- | ---- | ---- |
| packet_start_code_prefix | 24 | 总是`0x00 0x00 0x01` |
| stream_id | 8 | 总是`0xBD`，对应private_stream_1 |
| **PES_packet_length** | **16** | **PES包长度，大端序**<sup>1</sup> |
| '10' | 2 | 总是`0b10` |
| PES_scrambling_control | 2 | 总是`0b00` |
| PES_priority | 1 | 总是`0b1` |
| data_alignment_indicator | 1 | 总是`0b1` |
| copyright | 1 | 总是`0b0` |
| original_or_copy | 1 | 总是`0b0` |
| PTS_DTS_flags | 2 | 总是`0b10` |
| ESCR_flag | 1 | 总是`0b0` |
| ES_rate_flag | 1 | 总是`0b0` |
| DSM_trick_mode_flag | 1 | 总是`0b0` |
| additional_copy_info_flag | 1 | 总是`0b0` |
| PES_CRC_flag | 1 | 总是`0b0` |
| PES_extension_flag | 1 | 总是`0b0` |
| PES_header_data_length | 8 | 总是`0x07`<sup>2</sup> |
| '0010' | 4 | 总是`0b0010` |
| PTS \[32..30\] | 3 | PTS \[32..30\]，似乎总是`0b000`<sup>3</sup> |
| marker_bit | 1 | 总是`0b1` |
| PTS \[19..15\] | 15 | PTS \[19..15\] |
| marker_bit | 1 | 总是`0b1` |
| PTS \[14..0\] | 15 | PTS \[14..0\] |
| marker_bit | 1 | 总是`0b1` |
| stuffing_byte | 16 | 总是`0xFF 0xF8` |

<sup>1</sup> <span id="jump_pes_len">此处的PES包长度</span>的含义是PES_packet_length之后的一字节开始（含），到整个PES包的最后一字节（含）的长度。

<sup>2</sup> PES_header_data_length指的是PTS和stuffing_byte的长度之和，以字节为单位。

<sup>3</sup> PTS全称presentation time stamp，用来记录PES包的时间，每 $\frac{1}{90kHz}$ 增加1。详见ISO/IEC 13818-1 §2.4.3.7。

经过上表分析可知，header中会变化的只有两项：PTS和PES包长度。

<span id="jump_pts_timestamp">PTS和PES包出现的时间有关，可以将其当作一个行车记录仪内部的时间戳。行车记录仪的PTS总是可以整除90，从而得到一个以毫秒为单位的整数时间戳。</span>

PES包长度确定了后续data的长度。由于在PES包长度之后，data开始之前，header还有10个字节，因此所有private_stream_1的data长度可用`PES_packet_length - 10`表示。

### private_stream_1 PES_packet data

private_stream_1 PES_packet data包括了GPS、加速度计、红绿灯识别、前车起步识别等信息。其内部结构较为复杂。具体请参考[private_stream_1数据格式](./private_stream_1.md)。

观察发现：
- GPS数据记录频率为每秒1次。
- 加速度计数据包有两种。二进制形式大约每秒9次。文字形式每秒记录5次，每次记录与最近一次二进制数据相同。
- 停车时将会检测红绿灯以及前车移动情况，并记录。

<br/><br/>
返回[hivXXXXX.mp4 文件简介](./hiv_mp4.md)
