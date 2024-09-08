# private_stream_1数据格式

在[视频文件分段结构](./hiv_mp4_video.md#jump_pes_header)中，说明了所有private_stream_1 PES包都包括header和data两部分，也描述了header部分的含义。本文详细描述data部分含义。

private_stream_1的data部分包含了很多信息，到目前为止只有一小部分可以猜测出含义（GPS、加速度计等），剩余部分仍有待研究。

经过观察，在自定义的data部分，还有一个小header，后文称之为`private_header`。这个private_header之后的data称之为`private_data`，以和PES包的header和data作区分。因此整个PES包的data部分又可以分为两部分：

|  | 内容 |
| ---- | ---- |
| private_header | 包的类型，数据长度等 |
| private_data | 具体数据 |

## private_header

所有private_stream_1包data的开始部分都有一个长度固定为`0x0C`的private_header。private_header的内容用**大端序**表示，与内部private_data不同。

其结构如下：

| 偏移量 | 字节数 | 类型 | 猜测含义 |
| ---- | ---- | ---- | ---- |
| 0x00 | 2 | uint16 | 大端序，与数据内容有关，后文称之为`pkt_id` |
| 0x02 | 2 | uint16 | 大端序，数据长度<sup>1</sup>的四分之一，后文称之为`pkt_len` |
| 0x04 | 2 | uint16 | 大端序，与数据内容有关，后文称之为`sub_pkt_id` |
| 0x06 | 6 | NA | 不明，总是`0x81 0x00 0x00 0xFF 0x00 0x00` |

<sup>1</sup> 数据长度，指的是从sub_pkt_id的第1个字节（含）一直到本个private_stream_1包末尾（含）的长度。此处记录了数据长度的四分之一，数据长度总是4的整倍数。

参考[PES_packet_length含义](./hiv_mp4_video.md#jump_pes_len)，可知 $`PES\_packet\_length = pkt\_len * 4 + 14`$

## private_data

pkt_id和sub_pkt_id不同，则private_data所含内容和结构也不同。经过观察，id与private_data内容的对应如下表：

| pkt_id | sub_pkt_id | private_data内容 |
| ---- | ---- | ---- |
| 0x0007 | 0x0001 | [文字格式的加速度计数据](./private_ascii_acce.md) |
| 0x0802 | 0x0007 | [二进制格式加速度计/GPS数据](./private_bin_acce_gps.md) |
| 0x0802 | 0x0001 | [红绿灯、前车起步、GPS、加速度计等](./private_misc_1.md) |
| 0x0009 | 0x0001 | [红绿灯、加速度计等](./private_misc_2.md) |

在所有的文件中只观察到了这些pkt_id与sub_pkt_id的组合。

由于各类private_data内部结构较为复杂，这里分成不同的文档描述。请点击相应超链接参考某个id对应类型的private_data结构。

<br/><br/>
返回[视频文件分段结构](./hiv_mp4_video.md#jump_pes_private_stream_1)
