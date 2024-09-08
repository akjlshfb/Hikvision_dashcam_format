# pkt_id=0x0009 sub_pkt_id=0x0001 多种数据

这一类数据包与[上一类数据包](./private_misc_1.md)结构非常相似。很多数据完全相同。

这一类数据包也可以分为header和若干个部分。与上一类数据包相比，这一类数据包：
- 包header不同
- 不存在part_1和part_2
- part_3长度计算方式略有不同（虽然结构类似）
- 后面的part_4到part_8的含义与上一类数据包**完全相同**
- 频率同样也为每秒5个

数据包结构为：

|  | 长度是否可变 | 长度 | 包含信息 |
| ---- | ---- | ---- | ---- |
| [header](#jump_header_2) | 固定 | ***0x0010*** | 是否检测到前车起步/绿灯 |
| [part_3](#jump_part_3_2) | 可变 | [part_3_len](#jump_part_3_2) - ***0x0650***</br>停车时，总是`0x0644`</br>行车时，总是`0x03F8` | 不明</br>**注意part_3长度定义和上一类数据包不同** |
| [part_4](./private_misc_1.md#jump_part_4)| 固定 | 0x017C | 所有检测到的红绿灯在图像中的位置 |
| [part_5](./private_misc_1.md#jump_part_5) | 固定 | 0x0038 | 检测到红灯变绿时，绿灯在图像中位置 |
| [part_6](./private_misc_1.md#jump_part_6) | 固定 | 0x0084 | 之前11个加速度计数据 |
| [part_7](./private_misc_1.md#jump_part_7) | 固定 | 0x0404 | 不明 |
| [part_8](./private_misc_1.md#jump_part_8) | 固定 | 0x0028 | 不明 |

由于不存在可变长度的part_1，且仅有part_3长度可变，因此从长度来看，这类数据包只会有两种长度：
- 当停车时，其长度为`0x0CB8`
- 当行车时，其长度为`0x0A6C`

另外，如果本类数据包和上一类数据包在同一个Program Stream pack中出现（即同一帧，内部时间戳相同），则part_3到part_8将完全相同。

接下来，按照上表的划分，分别描述每一部分的结构。

## <span id="jump_header_2">header</span>

header长度固定为0x10。其结构见下表：

| 偏移量 | 字节数 | 类型 | 猜测含义 |
| ---- | ---- | ---- | ---- |
| 0x00 | 12 |  | private_header |
| 0x0C | 4 | char[] | 不明，总是`HKJI` |

## <span id="jump_part_3_2">part_3</span>

这一部分长度可变。停车时长为0x644，行车时长为0x3F8，相差了0x24C。其内容含义不明。

part_3长度总是`part_3_len - 0x650`。这里与上一类数据包不同，上一类中减去的数字是`0x64C`。`part_3_len`定义见下表：

| 偏移量 | 字节数 | 类型 | 猜测含义 |
| ---- | ---- | ---- | ---- |
| 0x0 | 4 | uint32 | 本个PES包的[内部时间戳](./private_ascii_acce.md#jump_timestamp) |
| 0x4 | 4 | NA | 不明 |
| 0x8 | 2 | uint16 | **part_3_len** |
| 0xA | 一直到part_3结尾</br>`part_3_len - 0x65A` | NA | 不明 |

## 其他part

其他part的含义都和[上一类数据包](./private_misc_1.md)相同，请参照相应文档。

<br/><br/>
返回[private_stream_1数据格式](./private_stream_1.md#private_data)
