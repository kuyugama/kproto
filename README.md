Yet another data transferring protocol

```python
from proto import primitives
import proto

class Profile(proto.ComplexDataType, id="user-profile"):
    first_name: primitives.String
    last_name: primitives.String
    age: primitives.UInt8
    female: primitives.Boolean

profile = Profile(first_name="Kuyugama", last_name="Hikamiya", age=24, female=False)

print(profile)  # Profile(first_name='Kuyugama', last_name='Hikamiya', age=24, female=False)
serialized = profile.serialize()

assert serialized == b'\x08\x00Kuyugama\x08\x00Hikamiya\x18\x00'

deserialized = Profile.deserialize(serialized)
print(deserialized)  # Profile(first_name='Kuyugama', last_name='Hikamiya', age=24, female=False)

assert Profile.deserialize(serialized) == profile

IntArray = primitives.Array[primitives.UInt8]

arr = IntArray(1, 2, 3)

assert arr.serialize() == b'\x03\x01\x02\x03'

arr.pop()

assert arr.serialize() == b'\x02\x01\x02'


ProfileArray = primitives.Array[Profile]

arr = ProfileArray()

arr.append(profile)

assert arr.serialize() == b'\x01\x08\x00Kuyugama\x08\x00Hikamiya\x18\x00'

assert ProfileArray.deserialize(arr.serialize()) \
       == primitives.Array[Profile](profile) \
       == [profile]
```