# Change log
## Version 0.0.2
+ Fix the error in `wait_result` of Session.
+ Remove ActiveSession and PassiveSession. Now csbuilder allows to create the protocol which has both active activation and passive activation.
+ Change size of elements in cspacket.
+ Add role to `CSPacket`. Now a `SessionManager` can contain multiple roles of a protocol.
+ Remove the `CSPacketUtils`. Instead, add `from_bytes` to `CSPacket` to extract the packet.


## Version 0.0.1
+ Hello world.