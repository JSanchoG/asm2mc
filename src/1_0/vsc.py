import os
import random
import re

# asm -> mca -> mc
# asm - assembler with mnemonic, labels etc.
# mca - (Machine Code Assembler) - machine code but with some assembler syntax
# mc - (Machine Code) - pure machine code
class VSC:
  memorySize = 10000 # Addresses from 0000 to 9999

  acc = None
  bp = 9999
  sp = 9999
  ip = None # instruction pointer
  #mar = None # memory address register
  #mbr = None # memory buffer register
  #ir = None # instruction register
  flags = {"zero": False, "negative": False}
  memory = None
  halted = None
  programInMemory = None


  def __init__(self):
    self.memory = [f"{random.randint(0, 99999):05d}" for i in range(self.memorySize)] # Fill memory with some random values
    # memory = random.sample(range(0, 99999+1), self.memorySize)

  def printAddressFromRanges(self, ranges, reverse = False):
    for r in ranges:
      if r["type"] == "number":
        i = r["position"]
        print(f"M[{i:04d}] = {self.memory[i]}")
      elif r["type"] == "range":
        if reverse:
          for i in range(r["end"], r["begin"]-1, -1):
            print(f"M[{i:04d}] = {self.memory[i]}")
        else:
          for i in range(r["begin"], r["end"]+1):
            print(f"M[{i:04d}] = {self.memory[i]}")

  def reset(self):
    self.memory = ["00000" for i in range(self.memorySize)]
    self.halted = False


  def setStartAddr(self, startAddr):
    self.ip = startAddr


  def bitsToInt(self, bits):
    sign = bits[0]
    v = None

    if sign == "0":
      v = int(bits[1:])
    else:
      v = (-1) * int(bits[1:])

    return v

  def intToBits(self, integer):
    bits = f"{integer:05d}"

    if integer<0:
      bits = '1' + bits[1:]

    return bits

  def getValueAtAddressAsBits(self, address):
    valueS = self.memory[address]
    return self.fillBitsToLength(valueS)


  def fillBitsToLength(self, bits):
    bitsN = bits
    l = len(bitsN)
    if l<5:
      bitsN = "0" * (5-l) + bitsN

    return bitsN


  def printAccumulatorInfo(self):
    print(f"Value in accumulator as bits: {self.acc}")
    v = self.printIntWithSign(self.bitsToInt(self.acc))
    print(f"Value in accumulator as int: {v}")


  def printIntWithSign(self, valueInt):
    if valueInt>0:
      return f"+{valueInt:04d}"
    return f"{valueInt:05d}"


  def updateFlags(self, valueBits):
    accV = self.bitsToInt(valueBits)
    self.flags["zero"] = False
    self.flags["negative"] = False

    if accV == 0:
      self.flags["zero"] = True
    elif accV < 0:
      self.flags["negative"] = True


  def checkIfStackPointersCorrect(self, operationType):
    if 'push':
      if self.sp-1 < 0:
        print("!!! General protection fault !!!")
        print("No free space on stack")
        print("Machine halted")
        self.halted = True
        return False
    elif 'pop':
      if self.sp+1 > self.bp:
        print("!!! General protection fault !!!")
        print("Access violation, try to reach beyond the stack base")
        print("Machine halted")
        self.halted = True
        return False
      elif self.sp == self.bp:
        print("!!! General protection fault !!!")
        print("Access violation, stack is empty")
        print("Try to reach beyond the stack base")
        print("Machine halted")
        self.halted = True
        return False

    return True

  def executeInstruction(self):
    if not self.programInMemory:
      print("There is no program in memory")
      return

    if self.halted:
      print("Program execution halted. Please do reset")
      return
    elif self.halted is None:
      self.halted = False

    instruction = self.memory[self.ip]

    print("Registers:")
    print(f"IR = {instruction}")
    print(f"BP = {self.bp:04d}")
    print(f"SP = {self.sp:04d}")
    print(f" A = {self.acc}")
    print(f"IP = {self.ip}")
    print("Flags:")
    for f in self.flags:
      print(f"{f:<8} = {self.flags[f]}")
    print("")

    if len(instruction) != 5:
      instruction = None

    if instruction[0] == "0":
      if instruction == "00000":
        print("Description: Stop the cpu.")
        print("Mnemonic: HLT")
        print("Machine code: 00000")
        self.halted = True
      elif instruction[0:2] == "01":
        address = int(instruction[2:5])
        valueBits = self.getValueAtAddressAsBits(address)
        valueInt = self.bitsToInt(valueBits)
        valueIntNew = valueInt + 1
        valueBitsNew = self.intToBits(valueIntNew)
        print("Description: Increase value at address aaa by 1, M[aaa] := M[aaa] + 1.")
        print("Mnemonic: INC aaa")
        print("Machine code: 01aaa")
        print("Addressing: direct")
        print(f"Old value at address {address:04d} as bits: {valueBits}")
        print(f"Old value at address {address:04d} as int: {self.printIntWithSign(valueInt)}")
        print(f"New value at address {address:04d} as bits: {valueBitsNew}")
        print(f"New value at address {address:04d} as int: {self.printIntWithSign(valueIntNew)}")
        self.memory[address] = valueBitsNew
        self.updateFlags(valueBitsNew)
        self.ip += 1
      elif instruction[0:2] == "02":
        address = int(instruction[2:5])
        valueBits = self.getValueAtAddressAsBits(address)
        valueInt = self.bitsToInt(valueBits)
        valueIntNew = valueInt - 1
        valueBitsNew = self.intToBits(valueIntNew)
        print("Description: Decrease value at address aaa by 1, M[aaa] := M[aaa] - 1.")
        print("Mnemonic: DEC aaa")
        print("Machine code: 02aaa")
        print("Addressing: direct")
        print(f"Old value at address {address:04d} as bits: {valueBits}")
        print(f"Old value at address {address:04d} as int: {self.printIntWithSign(valueInt)}")
        print(f"New value at address {address:04d} as bits: {valueBitsNew}")
        print(f"New value at address {address:04d} as int: {self.printIntWithSign(valueIntNew)}")
        self.memory[address] = valueBitsNew
        self.updateFlags(valueBitsNew)
        self.ip += 1
      elif instruction == "03000":
        # When you put something onto the stack (PUSH onto the stack),
        # the SP is decremented before the item is placed on the stack.
        print("Description: Push value from accumulator onto the stack, A -> STACK.")
        print("Mnemonic: PUSH")
        print("Machine code: 03000")
        print("Addressing: immediate")
        if self.checkIfStackPointersCorrect('push'):
          self.sp -= 1
          self.memory[self.sp] = self.acc
          valueBits = self.getValueAtAddressAsBits(self.sp)
          print(f"BP={self.bp:04d}")
          print(f"SP={self.sp:04d}")
          print(f"M[SP] as bits: {valueBits}")
          self.ip += 1
      elif instruction == "04000":
        # When you take something off of the stack (PULL from the stack),
        # the SP is incremented after the item is pulled from the stack
        print("Description: Pop value from the stack to accumulator, STACK -> A.")
        print("Mnemonic: POP")
        print("Machine code: 04000")
        print("Addressing: immediate")
        if self.checkIfStackPointersCorrect('pop'):
          valueBits = self.getValueAtAddressAsBits(self.sp)
          self.acc = valueBits
          self.sp += 1
          print(f"Value popped from the stack as bits: {valueBits}")
          print(f"BP={self.bp:04d}")
          print(f"SP={self.sp:04d}")
          self.printAccumulatorInfo()
          self.ip += 1
    elif instruction[0] == "1":
      address = int(instruction[1:5])
      valueBits = self.getValueAtAddressAsBits(address)
      print("Description: Copy value from memory at address aaaa to accumulator, A := M[aaaa].")
      print("Mnemonic: CPA aaaa")
      print("Machine code: 1aaaa")
      print("Addressing: direct")
      print(f"Value at address {address:04d}: {valueBits}")
      self.acc = valueBits
      self.printAccumulatorInfo()
      self.ip += 1
    elif instruction[0] == "2":
      address = int(instruction[1:5])
      valueBits = self.acc
      print("Description: Copy value from accumulator to memory at address aaaa, M[aaaa] := A.")
      print("Mnemonic: STO aaaa")
      print("Machine code: 2aaaa")
      print("Addressing: direct")
      print(f"Store at address {address:04d} value: {valueBits}")
      self.memory[address] = valueBits
      self.ip += 1
    elif instruction[0] == "3":
      address = int(instruction[1:5])
      valueBits = self.getValueAtAddressAsBits(address)
      valueInt = self.bitsToInt(valueBits)
      print("Description: Add value at specified address aaaa to accumulator. Result is stored in accumulator, A := A + M[aaaa].")
      print("Mnemonic: ADD aaaa")
      print("Machine code: 3aaaa")
      print("Addressing: direct")
      print(f"Address: {address:04d}")
      print(f"Value at address {address:04d} as bits: {valueBits}")
      print(f"Value at address {address:04d} as int: {self.printIntWithSign(valueInt)}")
      aInt = self.bitsToInt(self.acc)
      rInt = aInt + valueInt
      self.acc = self.intToBits(rInt)
      self.printAccumulatorInfo()
      self.updateFlags(self.acc)
      self.ip += 1
    elif instruction[0] == "4":
      address = int(instruction[1:5])
      valueBits = self.getValueAtAddressAsBits(address)
      valueInt = self.bitsToInt(valueBits)
      print("Description: Subtract value at specified address aaaa from accumulator. Result is stored in accumulator A := A - M[aaaa].")
      print("Mnemonic: SUB aaaa")
      print("Machine code: 4aaaa")
      print("Addressing: direct")
      print(f"Address: {address:04d}")
      print(f"Value at address {address:04d} as bits: {valueBits}")
      print(f"Value at address {address:04d} as int: {self.printIntWithSign(valueInt)}")
      aInt = self.bitsToInt(self.acc)
      rInt = aInt - valueInt
      self.acc = self.intToBits(rInt)
      self.printAccumulatorInfo()
      self.updateFlags(self.acc)
      self.ip += 1
    elif instruction[0] == "5":
      address = int(instruction[1:5])
      valueBits = self.getValueAtAddressAsBits(address)
      valueInt = self.bitsToInt(valueBits)
      print("Description: Multiply value from accumulator by value at specified address aaaa. Result is stored in accumulator A := A * M[aaaa].")
      print("Mnemonic: MUL aaaa")
      print("Machine code: 5aaaa")
      print("Addressing: direct")
      print(f"Address: {address:04d}")
      print(f"Value at address {address:04d} as bits: {valueBits}")
      print(f"Value at address {address:04d} as int: {self.printIntWithSign(valueInt)}")
      aInt = self.bitsToInt(self.acc)
      rInt = aInt * valueInt
      self.acc = self.intToBits(rInt)
      self.printAccumulatorInfo()
      self.updateFlags(self.acc)
      self.ip += 1
    elif instruction[0] == "6":
      address = int(instruction[1:5])
      print("Description: Unconditional branch to instruction located at address aaaa.")
      print("Mnemonic: BRA aaaa")
      print("Machine code: 6aaaa")
      print("Addressing: direct")
      print(f"Address: {address:04d}")
      self.ip = address
    elif instruction[0] == "7":
      address = int(instruction[1:5])
      print("Description: Conditional branch to instruction located at address aaaa if value stored in accumulator is negative.")
      print("Mnemonic: BRN aaaa")
      print("Machine code: 7aaaa")
      print("Addressing: direct")
      print(f"Address: {address:04d}")
      print(f"Value in accumulator: {self.acc}")
      isNegative = True

      if self.acc[0] == "0":
        isNegative = False

      if isNegative:
        self.ip = address
        print("Value in accumulator is negative")
      else:
        self.ip += 1
        print("Value in accumulator is positive")
    elif instruction[0] == "8":
      address = int(instruction[1:5])
      print("Description: Conditional branch to instruction located at address aaaa if value stored in accumulator is equal to zero.")
      print("Mnemonic: BRZ aaaa")
      print("Machine code: 8aaaa")
      print("Addressing: direct")
      print(f"Address: {address:04d}")
      print(f"Value in accumulator: {self.acc}")
      isZero = False

      if self.acc[1:5] == "0000": # I don't care about sign
        isZero = True

      if isZero:
        self.ip = address
        print("Value in accumulator is equal to zero")
      else:
        self.ip += 1
        print("Value in accumulator is not equal to zero")

    elif instruction[0] == "9":
      if instruction[0:3] == "907":
        address = int(instruction[3:5])
        print("Description: Conditional branch to instruction located at address aa if flag NEGATIVE is TRUE.")
        print("Mnemonic: BRNF aa")
        print("Machine code: 907aa")
        print("Addressing: direct")
        print(f"Address: {address:04d}")
        print(f"NEGATIVE flag: {self.flags['negative']}")
        isNegative = self.flags['negative']

        if isNegative:
          self.ip = address
          print("NEGATIVE flag is set")
        else:
          self.ip += 1
          print("NEGATIVE flag is NOT set")
      elif instruction[0:3] == "908":
        address = int(instruction[3:5])
        print("Description: Conditional branch to instruction located at address aa if flag ZERO is TRUE.")
        print("Mnemonic: BRZF aa")
        print("Machine code: 908aa")
        print("Addressing: direct")
        print(f"Address: {address:04d}")
        print(f"NEGATIVE flag: {self.flags['zero']}")
        isNegative = self.flags['zero']

        if isNegative:
          self.ip = address
          print("ZERO flag is set")
        else:
          self.ip += 1
          print("ZERO flag is NOT set")
      elif instruction == "91030":
        self.ip += 1
        address = int(self.memory[self.ip])
        addressBits = self.getValueAtAddressAsBits(address)
        address = self.bitsToInt(addressBits)
        valueBits = self.getValueAtAddressAsBits(address)
        print("Description: Push value at address aaaaa onto the stack, M[aaaaa] -> STACK.")
        print("Mnemonic: PUSH aaaaa")
        print("Machine code: 91030 aaaaa")
        print("Addressing: direct, two byte length")
        print(f"Value at address {addressBits} as bits: {valueBits}")
        if self.checkIfStackPointersCorrect('push'):
          self.sp -= 1
          self.memory[self.sp] = valueBits
          valueBits = self.getValueAtAddressAsBits(self.sp)
          print(f"BP={self.bp:04d}")
          print(f"SP={self.sp:04d}")
          print(f"M[SP] as bits: {valueBits}")
          self.ip += 1
      elif instruction == "91040":
        self.ip += 1
        address = int(self.memory[self.ip])
        print("Description: Pop value from the stack and put at address aaaaa, STACK -> M[aaaaa].")
        print("Mnemonic: POP aaaaa")
        print("Machine code: 91040 aaaaa")
        print("Addressing: direct, two byte length")
        if self.checkIfStackPointersCorrect('push'):
          valueBits = self.getValueAtAddressAsBits(self.sp)
          self.memory[address] = valueBits
          self.sp += 1
          print(f"Value popped from the stack as bits: {valueBits}")
          print(f"BP={self.bp:04d}")
          print(f"SP={self.sp:04d}")
          self.ip += 1
      elif instruction[0:3] == "921":
        valueBits = instruction[3:5]
        print("Description: Copy exact value ss to accumulator, A := ss.")
        print("Mnemonic: CPA (ss)")
        print("Machine code: 921ss")
        print("Addressing: immediate, one byte length")
        print(f"Value: {valueBits}")
        self.acc = valueBits
        self.printAccumulatorInfo()
        self.ip += 1
      elif instruction == "93030":
        self.ip += 1
        valueBits = self.getValueAtAddressAsBits(self.ip)
        print("Description: Push exact value sssss onto the stack, sssss -> STACK.")
        print("Mnemonic: PUSH (sssss)")
        print("Machine code: 93030 sssss")
        print("Addressing: immediate, two byte length")
        print(f"Value: {valueBits}")
        if self.checkIfStackPointersCorrect('push'):
          self.sp -= 1
          self.memory[self.sp] = valueBits
          valueBits = self.getValueAtAddressAsBits(self.sp)
          print(f"BP={self.bp:04d}")
          print(f"SP={self.sp:04d}")
          print(f"M[SP] as bits: {valueBits}")
          self.ip += 1
      elif instruction == "93100":
        self.ip += 1
        valueBits = self.getValueAtAddressAsBits(self.ip)
        print("Description: Copy exact value sssss (located in next byte) to accumulator, A := sssss.")
        print("Mnemonic: CPA (sssss)")
        print("Machine code: 93100 sssss")
        print("Addressing: immediate, two byte length")
        print(f"Value: {valueBits}")
        self.acc = valueBits
        self.printAccumulatorInfo()
        self.ip += 1
      elif instruction[0:3] == "941":
        address = int(instruction[3:5])
        addressBits = self.getValueAtAddressAsBits(address)
        address = self.bitsToInt(addressBits)
        valueBits = self.getValueAtAddressAsBits(address)
        print("Description: Copy value from memory at address given in memory at address aa to accumulator, A := M[M[aa]].")
        print("Mnemonic: CPA [aa]")
        print("Machine code: 941aa")
        print("Addressing: indirect, one byte length")
        print(f"Value: {valueBits}")
        self.acc = valueBits
        self.printAccumulatorInfo()
        self.ip += 1
      elif instruction == "95030":
        self.ip += 1
        address = int(self.memory[self.ip])
        addressBits = self.getValueAtAddressAsBits(address)
        address = self.bitsToInt(addressBits)
        valueBits = self.getValueAtAddressAsBits(address)
        print("Description: Push value at address specified at address aaaaa onto the stack, M[M[aaaaa]] -> STACK.")
        print("Mnemonic: PUSH [aaaaa]")
        print("Machine code: 95030 aaaaa")
        print("Addressing: indirect, two byte length")
        print(f"Value: {valueBits}")
        if self.checkIfStackPointersCorrect('push'):
          self.sp -= 1
          self.memory[self.sp] = valueBits
          valueBits = self.getValueAtAddressAsBits(self.sp)
          print(f"BP={self.bp:04d}")
          print(f"SP={self.sp:04d}")
          print(f"M[SP] as bits: {valueBits}")
          self.ip += 1
      elif instruction == "95040":
        self.ip += 1
        address = int(self.memory[self.ip])
        addressBits = self.getValueAtAddressAsBits(address)
        address = self.bitsToInt(addressBits)
        print("Description: Pop value from the stack and put at address specified at address aaaaa, STACK -> M[M[aaaaa]].")
        print("Mnemonic: POP aaaaa")
        print("Machine code: 95040 aaaaa")
        print("Addressing: direct, two byte length")
        if self.checkIfStackPointersCorrect('pop'):
          valueBits = self.getValueAtAddressAsBits(self.sp)
          self.memory[address] = valueBits
          self.sp += 1
          print(f"Value popped from the stack as bits: {valueBits}")
          print(f"BP={self.bp:04d}")
          print(f"SP={self.sp:04d}")
          self.ip += 1
      elif instruction == "95100":
        self.ip += 1
        address = int(self.memory[self.ip])
        addressBits = self.getValueAtAddressAsBits(address)
        address = self.bitsToInt(addressBits)
        valueBits = self.getValueAtAddressAsBits(address)
        print("Description: Copy value from memory at address given in memory at address aaaaa to accumulator, A := M[M[aaaaa]].")
        print("Mnemonic: CPA [aaaaa]")
        print("Machine code: 95100 aaaaa")
        print("Addressing: indirect, two byte length")
        print(f"Value: {valueBits}")
        self.acc = valueBits
        self.printAccumulatorInfo()
        self.ip += 1
      elif instruction[0:3] == "942":
        address = int(instruction[3:5])
        addressBits = self.getValueAtAddressAsBits(address)
        address = self.bitsToInt(addressBits)
        valueBits = self.acc
        print("Description: Copy value from accumulator to memory at address given in memory at address aa, M[M[aa]] := A.")
        print("Mnemonic: STO [aa]")
        print("Machine code: 942aa")
        print("Addressing: indirect, one byte length")
        print(f"Store at address {address:04d} value: {valueBits}")
        self.memory[address] = valueBits
        self.ip += 1
      elif instruction == "95200":
        self.ip += 1
        address = int(self.memory[self.ip])
        addressBits = self.getValueAtAddressAsBits(address)
        address = self.bitsToInt(addressBits)
        valueBits = self.acc
        print("Description: Copy value from accumulator to memory at address given in memory at address aaaaa, M[M[aaaaa]] := A.")
        print("Mnemonic: STO [aaaaa]")
        print("Machine code: 95200 aaaaa")
        print("Addressing: indirect, two byte length")
        print(f"Store at address {address:04d} value: {valueBits}")
        self.memory[address] = valueBits
        self.ip += 1
      elif instruction[0:3] == "923":
        valueBits = instruction[3:5]
        valueInt = self.bitsToInt(valueBits)
        print("Description: Add exact value ss to accumulator. Result is stored in accumulator, A := A + ss.")
        print("Mnemonic: ADD (ss)")
        print("Machine code: 923ss")
        print("Addressing: immediate, one byte length")
        print(f"Value as bits: {valueBits}")
        print(f"Value as int: {self.printIntWithSign(valueInt)}")
        aInt = self.bitsToInt(self.acc)
        rInt = aInt + valueInt
        self.acc = self.intToBits(rInt)
        self.printAccumulatorInfo()
        self.updateFlags(self.acc)
        self.ip += 1
      elif instruction == "93300":
        self.ip += 1
        valueBits = self.getValueAtAddressAsBits(self.ip)
        valueInt = self.bitsToInt(valueBits)
        print("Description: Add exact value sssss (located in next byte) to accumulator. Result is stored in accumulator, A := A + sssss.")
        print("Mnemonic: ADD (sssss)")
        print("Machine code: 93300 sssss")
        print("Addressing: indirect, two byte length")
        print(f"Value as bits: {valueBits}")
        print(f"Value as int: {self.printIntWithSign(valueInt)}")
        aInt = self.bitsToInt(self.acc)
        rInt = aInt + valueInt
        self.acc = self.intToBits(rInt)
        self.printAccumulatorInfo()
        self.updateFlags(self.acc)
        self.ip += 1
      elif instruction[0:3] == "943":
        address = int(instruction[3:5])
        addressBits = self.getValueAtAddressAsBits(address)
        address = self.bitsToInt(addressBits)
        valueBits = self.getValueAtAddressAsBits(address)
        valueInt = self.bitsToInt(valueBits)
        print("Description: Add value from memory at address given in memory at address aa to accumulator, A := A + M[M[aa]].")
        print("Mnemonic: ADD [aa]")
        print("Machine code: 943aa")
        print("Addressing: indirect, one byte length")
        print(f"Value as bits: {valueBits}")
        print(f"Value as int: {self.printIntWithSign(valueInt)}")
        aInt = self.bitsToInt(self.acc)
        rInt = aInt + valueInt
        self.acc = self.intToBits(rInt)
        self.printAccumulatorInfo()
        self.updateFlags(self.acc)
        self.ip += 1
      elif instruction == "95300":
        self.ip += 1
        address = int(self.memory[self.ip])
        addressBits = self.getValueAtAddressAsBits(address)
        address = self.bitsToInt(addressBits)
        valueBits = self.getValueAtAddressAsBits(address)
        valueInt = self.bitsToInt(valueBits)
        print("Description: Add value from memory at address given in memory at address aaaaa to accumulator, A := A + M[M[aaaaa]].")
        print("Mnemonic: ADD [aaaaa]")
        print("Machine code: 95300 aaaaa")
        print("Addressing: indirect, two byte length")
        print(f"Value as bits: {valueBits}")
        print(f"Value as int: {self.printIntWithSign(valueInt)}")
        aInt = self.bitsToInt(self.acc)
        rInt = aInt + valueInt
        self.acc = self.intToBits(rInt)
        self.printAccumulatorInfo()
        self.updateFlags(self.acc)
        self.ip += 1
      elif instruction[0:3] == "924":
        valueBits = instruction[3:5]
        valueInt = self.bitsToInt(valueBits)
        print("Description: Subtract exact value ss from accumulator. Result is stored in accumulator, A := A - ss.")
        print("Mnemonic: SUB (ss)")
        print("Machine code: 924ss")
        print("Addressing: immediate, one byte length")
        print(f"Value as bits: {valueBits}")
        print(f"Value as int: {self.printIntWithSign(valueInt)}")
        aInt = self.bitsToInt(self.acc)
        rInt = aInt - valueInt
        self.acc = self.intToBits(rInt)
        self.printAccumulatorInfo()
        self.updateFlags(self.acc)
        self.ip += 1
      elif instruction == "93400":
        self.ip += 1
        valueBits = self.getValueAtAddressAsBits(self.ip)
        valueInt = self.bitsToInt(valueBits)
        print("Description: Subtract exact value sssss (located in next byte) from accumulator. Result is stored in accumulator, A := A - sssss.")
        print("Mnemonic: SUB (sssss)")
        print("Machine code: 93400 sssss")
        print("Addressing: indirect, two byte length")
        print(f"Value as bits: {valueBits}")
        print(f"Value as int: {self.printIntWithSign(valueInt)}")
        aInt = self.bitsToInt(self.acc)
        rInt = aInt - valueInt
        self.acc = self.intToBits(rInt)
        self.printAccumulatorInfo()
        self.updateFlags(self.acc)
        self.ip += 1
      elif instruction[0:3] == "944":
        address = int(instruction[3:5])
        addressBits = self.getValueAtAddressAsBits(address)
        address = self.bitsToInt(addressBits)
        valueBits = self.getValueAtAddressAsBits(address)
        valueInt = self.bitsToInt(valueBits)
        print("Description: Subtract value from memory at address given in memory at address aa from accumulator, A := A + M[M[aa]].")
        print("Mnemonic: SUB [aa]")
        print("Machine code: 944aa")
        print("Addressing: indirect, one byte length")
        print(f"Value as bits: {valueBits}")
        print(f"Value as int: {self.printIntWithSign(valueInt)}")
        aInt = self.bitsToInt(self.acc)
        rInt = aInt - valueInt
        self.acc = self.intToBits(rInt)
        self.printAccumulatorInfo()
        self.updateFlags(self.acc)
        self.ip += 1
      elif instruction == "95400":
        self.ip += 1
        address = int(self.memory[self.ip])
        addressBits = self.getValueAtAddressAsBits(address)
        address = self.bitsToInt(addressBits)
        valueBits = self.getValueAtAddressAsBits(address)
        valueInt = self.bitsToInt(valueBits)
        print("Description: Subtract value from memory at address given in memory at address aaaaa from accumulator, A := A - M[M[aaaaa]].")
        print("Mnemonic: SUB [aaaaa]")
        print("Machine code: 95400 aaaaa")
        print("Addressing: indirect, two byte length")
        print(f"Value as bits: {valueBits}")
        print(f"Value as int: {self.printIntWithSign(valueInt)}")
        aInt = self.bitsToInt(self.acc)
        rInt = aInt - valueInt
        self.acc = self.intToBits(rInt)
        self.printAccumulatorInfo()
        self.updateFlags(self.acc)
        self.ip += 1
      elif instruction[0:3] == "925":
        valueBits = instruction[3:5]
        valueInt = self.bitsToInt(valueBits)
        print("Description: Multiply value from accumulator by exact value ss. Result is stored in accumulator, A := A * ss.")
        print("Mnemonic: MUL (ss)")
        print("Machine code: 925ss")
        print("Addressing: immediate, one byte length")
        print(f"Value as bits: {valueBits}")
        print(f"Value as int: {self.printIntWithSign(valueInt)}")
        aInt = self.bitsToInt(self.acc)
        rInt = aInt * valueInt
        self.acc = self.intToBits(rInt)
        self.printAccumulatorInfo()
        self.updateFlags(self.acc)
        self.ip += 1
      elif instruction == "93500":
        self.ip += 1
        valueBits = self.getValueAtAddressAsBits(self.ip)
        valueInt = self.bitsToInt(valueBits)
        print("Description: Multiply value from accumulator by exact value ss (located in next byte). Result is stored in accumulator, A := A * sssss.")
        print("Mnemonic: MUL (sssss)")
        print("Machine code: 93500 sssss")
        print("Addressing: indirect, two byte length")
        print(f"Value as bits: {valueBits}")
        print(f"Value as int: {self.printIntWithSign(valueInt)}")
        aInt = self.bitsToInt(self.acc)
        rInt = aInt * valueInt
        self.acc = self.intToBits(rInt)
        self.printAccumulatorInfo()
        self.updateFlags(self.acc)
        self.ip += 1
      elif instruction[0:3] == "945":
        address = int(instruction[3:5])
        addressBits = self.getValueAtAddressAsBits(address)
        address = self.bitsToInt(addressBits)
        valueBits = self.getValueAtAddressAsBits(address)
        valueInt = self.bitsToInt(valueBits)
        print("Description: Multiply value from accumulator by value from memory at address given in memory at address aa, A := A * M[M[aa]].")
        print("Mnemonic: MUL [aa]")
        print("Machine code: 945aa")
        print("Addressing: indirect, one byte length")
        print(f"Value as bits: {valueBits}")
        print(f"Value as int: {self.printIntWithSign(valueInt)}")
        aInt = self.bitsToInt(self.acc)
        rInt = aInt * valueInt
        self.acc = self.intToBits(rInt)
        self.printAccumulatorInfo()
        self.updateFlags(self.acc)
        self.ip += 1
      elif instruction == "95500":
        self.ip += 1
        address = int(self.memory[self.ip])
        addressBits = self.getValueAtAddressAsBits(address)
        address = self.bitsToInt(addressBits)
        valueBits = self.getValueAtAddressAsBits(address)
        valueInt = self.bitsToInt(valueBits)
        print("Description: Multiply value from accumulator by value from memory at address given in memory at address aaaaa, A := A * M[M[aaaaa]].")
        print("Mnemonic: MUL [aaaaa]")
        print("Machine code: 95500 aaaaa")
        print("Addressing: indirect, two byte length")
        print(f"Value as bits: {valueBits}")
        print(f"Value as int: {self.printIntWithSign(valueInt)}")
        aInt = self.bitsToInt(self.acc)
        rInt = aInt * valueInt
        self.acc = self.intToBits(rInt)
        self.printAccumulatorInfo()
        self.updateFlags(self.acc)
        self.ip += 1
    else:
      print("Unknown instruction")
      self.halted = True



  def executeProgram(self):
    safety = 100
    while True:
      self.executeInstruction()
      if self.halted:
        break
      safety -= 1

    if safety == 0:
      print("Maximum iteration limit reached.")
      print("If your program is not halted, repeat -run command.")



  def load(self, path):
    parts = path.split(".")
    extension = parts[-1]
    if extension == "mc":
      self.programInMemory = self.loadMC(path)
      if self.programInMemory:
        self.halted = False


  def loadMC(self, path):
    # The main difference between exists() and isfile() is that exists()
    # will return True if the given path to a folder or a file exists,
    # whereas isfile() returns True only if the given path is a path to
    # a file and not a folder.
    if not os.path.isfile(path):
      print(f"Cannot load {path} file")
      print(f"File {path} doesn't exist")
      return False

    with open(path, encoding="utf8") as fileSrc:
      lines = fileSrc.readlines()
      #print(lines)
      linesNormalized = []
      for l in lines:
        ln = l.split(";")[0].strip()
        ln = re.sub(r"\s", ' ', ln)  # The \s metacharacter matches whitespace character.
                                     # Whitespace characters can be: A space character.
                                     # A tab character. A carriage return character.
        ln = re.sub(r" +", ' ', ln)
        if len(ln):
          linesNormalized.append(ln)
      lines = linesNormalized
      #print(lines)
      # Put code into memory
      for l in lines:
        lParts = l.split()
        if len(lParts) == 2:
          address = lParts[0]
          instruction = lParts[1]

          if address.isnumeric() and instruction.isnumeric():
            address = int(address)

            if address <0 or address >= self.memorySize:
              print(f"Address out of range (0,{self.memorySize-1})")
              return False

            self.memory[address] = instruction
          else:
            print(f"Incorrect address ({address}) or instruction ({instruction}) in the following line:")
            print(l)
            return False

      return True

    print("Problems during file loading have occured")
    return False


def processCommandLine(commandsLine, listOfSwitch):
  #if len(sys.argv) == 1:
  #  return
  #
  #commandsList = sys.argv
  #
  nAll = len(commandsLine)

  #listOfSwitch = ["-path", "-tag", "-type", "-h"]
  commandsListTmp = []
  commandListUnknown = []
  
  for index, item in enumerate(commandsLine):
    if item in listOfSwitch:
      commandsListTmp.append({"key": item, "start": index, "end": index})
    elif item.startswith("-"):
      commandListUnknown.append(item)

  if len(commandListUnknown) > 0:
    print("Unknown options:")
    for opt in commandListUnknown:
      print(opt)
    return {}

  commandsList = commandsListTmp

  n = len(commandsList)

  if n > 0:
    for i in range(n-1):
      # There must be at least one element between two switches at position i and i+1
      if commandsList[i]["start"]+1 < commandsList[i+1]["start"]:
        commandsList[i]["start"] = commandsList[i]["start"] + 1
        commandsList[i]["end"] = commandsList[i+1]["start"] - 1
      else:#commandsList[i]["start"] > commandsList[i]["end"]:
        commandsList[i]["start"] = None
        commandsList[i]["end"] = None
        
    # There must be at least one element after last switch
    if commandsList[n-1]["start"] < nAll:
      commandsList[n-1]["start"] = commandsList[n-1]["start"] + 1
      commandsList[n-1]["end"] = nAll-1
    else:#if commandsList[n-1]["start"] > commandsList[n-1]["end"]:
      commandsList[n-1]["start"] = None
      commandsList[n-1]["end"] = None

  commandsDict = {}
  for command in commandsList:
    key = command["key"]
    if command["start"] is None:
      args = None
    else:
      args = commandsLine[command["start"]:command["end"]+1]
    commandsDict[key] = args

  return commandsDict

def parseRanges(args):
  ranges = []
  for i in range(len(args)):
    t = args[i]
    t = re.sub(r"[\s,]", '', t)
    t = t.split("-")
    if len(t) == 1 and t[0].isnumeric():
      t = {"type": "number", "position": int(t[0])}
      ranges.append(t)
    elif len(t) == 2 and t[0].isnumeric() and t[1].isnumeric():
      t = {"type": "range", "begin": int(t[0]), "end": int(t[1])}
      ranges.append(t)

  return ranges

def mainLoop():
  lastCommand = ""
  vsc = VSC()

  while(True):
    line = input("> ")

    if len(line) == 0:
      line = lastCommand
    else:
      lastCommand = line

    commandsList = line.split()
    listOfSwitch = ["-exit", "-h", "-load", "-memory", "-reset", "-run",
                     "-show", "-stack", "-startAddr", "-step"]
    commandsDict = processCommandLine(commandsList, listOfSwitch)

    #print(commandsDict)

    if '-exit' in commandsDict:
      break
    elif '-h' in commandsDict:
      printCommandHelp()
    elif '-load' in commandsDict: # tutu
      args = commandsDict['-load']
      if args and len(args) == 1:
        path = args[0]
        vsc.load(path)
        print(f"Program loaded from: {path}")
      else:
        print("Are you sure that you provide a PATH? Type -h for help if you need it.")
    elif '-reset' in commandsDict:
      vsc.reset()
      print("Set memory and registers to zeros. Done.")
    elif '-run' in commandsDict:
      if '-step' in commandsDict:
        print("Executing one instruction")
        vsc.executeInstruction()
      else:
        print("Executing code (max. 100 instructions)")
        vsc.executeProgram()
    elif '-show' in commandsDict:  # tutu
      if '-memory' in commandsDict:
        args = commandsDict['-memory']
        if args and len(args) > 0:
          ranges = parseRanges(args)
          vsc.printAddressFromRanges(ranges)
        else:
          print("Are you sure that you provide a RANGE? Type -h for help if you need it.")
      elif '-stack' in commandsDict:
        diff = vsc.sp - vsc.bp
        print(f"BP={vsc.bp:04d}")
        print(f"SP={vsc.sp:04d}")
        if diff == 0:
          print("Stack is empty")
        else:
          vsc.printAddressFromRanges(ranges, reverse=True)
      else:
        print("Specify what you want to see. Type -h for help if you need it.")
    elif '-startAddr' in commandsDict:
      args = commandsDict['-startAddr']
      if args and len(args) == 1:
        address = args[0]
        if address.isnumeric():
          vsc.setStartAddr(int(address))
          print(f"Starting at address: {address}")
        else:
          print("Addres must be a number")
      else:
        print("Are you sure that you provide an ADDRESS? Type -h for help if you need it.")
    else:
      print("Unknown command. Type -h for help if you need it.")


def printWelcomeMsg():
  text = \
'''
Welcome to VSCA (Very Simple Computer Assembler)
Version 1.0
Build 202411302232
Type -h and confirm with ENTER for help.
'''

  print(text)


def printCommandHelp():
  text = \
'''
-exit                - exit from VSCA
-h                   - print help
-load PATH           - load code from PATH
-reset               - set memory and registers to zeros
-run                 - execute program
-run -step           - execute one step of program
-show -labels        - show all labels (not implemented)
-show -labels LABELS - show selected LABELS (not implemented)
-show -memory RANGE  - show memory cells from RANGR
-show -stack         - print the stack
-startAddr ADDRESS   - set instruction pointer to address ADDRESS;
                       this way you specify instruction which
                       should be executed as next
ADDRESS              - decimal number from 0 to 9999
LABELS               -
PATH                 - path to program you want to execute
RANGE                - example: 1, 5, 10-15 specify numbers 1, 5 and all
                       numbers from 10 to 15

ENTER                - press ENTER to repeat last command
'''

  print(text)


if __name__ == '__main__':
  printWelcomeMsg()
  mainLoop()
