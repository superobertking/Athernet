- physical layer

  - 信号传输：48,000hz采样率，8kHz载波频率（6个采样/周期）
  - 编码/解码：尝试过4b5b（LUT实现）（效果不突出）
  - 调制/解调：(~~ASK~~/~~FSK~~/PSK) 将点乘结果按0分界，1 symbol/cycle
    - Challenge
      - preamble对齐
      - symbol对齐
    - Solution
      - preamble乱搞
      - 统计历史数据（proj1中实现）
      - 动态修正（proj2中实现）
  - performance
    - 8kbps，传输6250B文件需6.25s，可以使用2 symbol/cycle，仅需3.125s（典型值）
  - Error Correction
    - length: reedsolo
    - data field: CRC

  ​

- data layer

  - 帧
    - 类型：PING PONG（**吐槽**）ACK（802.11 CSMA/CA需要，但写的是CSMA **吐槽+**） START DATA
    - 长度：64KB*255 ≈ 16MB >> TCP包长度限制
    - 分帧
      - data size  = MTU - head size
      - START + DATA*
  - Stop and wait
  - Sliding window
  - LT fountain
  - 接收方状态机（figure）
    - limitation：同一时刻只能传同一个IP包（同步问题，tunnel）
  - PriorityQueue
    - ACK: high
    - DATA, PING, PONG: normal
  - Multi-level Random Queue
  - CSMA/CD：口糊



- network layer
  - thin layer
  - IP（header[type] + IP addr）
  - static ARP



- transport layer
  - aocket
    - ICMP
      - Echo request/reply
      - structure
      - problem
        - endian（checksum）
        - ICMP ID
        - Linux payload（the first 32 bits are datetime）
    - UDP
      - port（***each one is dedicated for an application***）
      - structure
    - toyTCP
      - SYN/FIN/~~ACK~~/DATA
      - structure



- application layer
  - FTP（***implemented on node1***）
    - state machine
    - multiple port



- Cross layer
  - NAT
    - MPLS-like
    - dynamical mapping
    - mutliple port listening
    - ​
  - tunnel
    - sock5 proxy



- Auxiliary
  - plot wave
  - save and replay