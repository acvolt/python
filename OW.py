#!/usr/bin/python

import smbus
import time
import ctypes
class OW(object):
	def DS2482_COMMAND_RESET(self):
		return 0xF0;
	def DS2482_COMMAND_SRP(self):
		return 0xE1
	def DS2482_POINTER_STATUS(self):
		return 0xF0
	def DS2482_STATUS_BUSY(self):
		return (1<<0)
	def DS2482_STATUS_PPD(self):
		return (1<<1)
	def DS2482_STATUS_SD(self):
		return (1<<2)
	def DS2482_STATUS_LL(self):
		return (1<<3)
	def DS2482_STATUS_RST(self):
		return (1<<4)
	def DS2482_STATUS_SBR(self):
		return (1<<5)
	def DS2482_STATUS_TSB(self):
		return (1<<6)
	def DS2482_STATUS_DIR(self):
		return (1<<7)	

	def DS2482_POINTER_DATA(self):
		return 0xE1
	def DS2482_POINTER_CONFIG(self):
		return 0xC3
	def DS2482_CONFIG_APU(self):
		return (1<<0)
	def DS2482_CONFIG_SPU(self):
		return (1<<2)
	def DS2482_CONFIG_1WS(self):
		return (1<<3)
	def DS2482_COMMAND_WRITECONFIG(self):
		return 0xD2
	def DS2482_COMMAND_RESETWIRE(self):
		return 0xb4
	def DS2482_COMMAND_WRITEBYTE(self):
		return 0xa5
	def DS2482_COMMAND_READBYTE(self):
		return 0x96
	def DS2482_COMMAND_SINGLEBIT(self):
		return 0x87
	def DS2482_COMMAND_TRIPLET(self):
		return 0x78

	def WIRE_COMMAND_SKIP(self):
		return 0xcc
	def WIRE_COMMAND_SELECT(self):
		return 0x55
	def WIRE_COMMAND_SEARCH(self):
		return 0xF0

	def DS2482_ERROR_TIMEOUT(self):
		return (1<<0)
	def DS2482_ERROR_SHORT(self):
		return (1<<1)
	def DS2482_ERROR_CONFIG(self):
		return (1<<2)

	def OW_READ_ROM(self):
		return 0x33
	def OW_MATCH_ROM(self):
		return 0x55
	def OW_SKIP_ROM(self):
		return 0xCC

	def DS18B20_CONVERT(self):
		return 0x44
	def DS18B20_WRITE_SCRATCHPAD(self):
		return 0x4e
	def DS18B20_READ_SCRATCHPAD(self):
		return 0xbe
	def DS18B20_COPY_SCRATCHPAD(self):
		return 0x48
	def DS18B20_RECALL_EEPROM(self):
		return 0xb8
	def DS18B20_READ_POWER(self):
		return 0xB4
	def DS18B20_ALARM_SEARCH(self):
		return 0xEC

	def DEVICE_DISCONNECTED_C(self):
		return -127
	def DEVICE_DISCONNECTED_F(self):
		return -196.6
	def DEVICE_DISCONNECTED_RAW(self):
		return -7040

	def getAddress(self):
		return self.address
	
	def deviceReset(self):
		status = 0
		owb = False
		
		#this is where we need to read a reg byte
		self.bus.read_byte_data(self.address, self.DS2482_COMMAND_RESET())
		
		#need a do while loop

		status = self.bus.read_byte(self.address)
		owb = status & self.DS2482_STATUS_BUSY()
		
		print "OWB="
		print bin(owb)
		print "\n"

	def setReadPointer(self, pointer):
		self.bus.write_byte_data(self.address, self.DS2482_COMMAND_SRP(), pointer)
	
	def readStatus(self):
		
		self.setReadPointer( self.DS2482_POINTER_STATUS())
		status = self.bus.read_byte(self.address)
#		print "\n Status is "
#		print bin(status)
		return status


	def readData(self):
		self.setReadPointer(self.DS2482_POINTER_DATA())
		return self.bus.read_byte(self.address)
	def readConfig(self):
		self.setReadPointer(self.DS2482_POINTER_CONFIG())
		return self.bus.read_byte(self.address)
	def setStrongPullup(self):
		self.writeConfig(self.readConfig() | self.DS2482_CONFIG_SPU())

	def clearStrongPullup(self):
		self.writeConfig(self.readConfig() & (~ self.DS2482_CONFIG_SPU()))

	def waitOnBusy(self):
		for x in range(0, 1000):
			status = self.readStatus()
			if (((~status) & self.DS2482_STATUS_BUSY())>0):
				break
		return status

	def writeConfig(self, config):
		self.waitOnBusy()
		config = (config | (~config) << 4)
		self.bus.write_byte_data(self.address, self.DS2482_COMMAND_WRITECONFIG(), config)
	def wireReset(self):
		self.waitOnBusy()
		self.clearStrongPullup()
		self.waitOnBusy()
		
		self.bus.read_byte_data(self.address, self.DS2482_COMMAND_RESETWIRE())
		
		status = self.waitOnBusy()
		if status & self.DS2482_STATUS_SD():
			print "Bus Shorted?"
		return True if (status & self.DS2482_STATUS_PPD()) else False
	def wireWriteByte(self, data, power):
		self.waitOnBusy()
		if power:
			setStrongPullup()
		self.bus.write_byte_data(self.address, self.DS2482_COMMAND_WRITEBYTE(), data)

	def wireReadByte(self):
		self.waitOnBusy()
		self.bus.write_byte(self.address, self.DS2482_COMMAND_READBYTE())
		self.waitOnBusy()
		self.setReadPointer(self.DS2482_POINTER_DATA())
		return self.bus.read_byte(self.address)

	
	
	def OWFirst(self):
		self.LastDiscrepancy = 0
		self.LastDeviceFlag = False
		self.LastFamilyDiscrepancy = 0
		return self.OWSearch();
	
	def OWNext(self):
		return self.OWSearch();

	def OWSearch(self):
		#initialize search parameters
		id_bit_number = 1
		last_zero = 0
		rom_byte_number = 0
		rom_byte_mask = 1
		search_result = 0
		self.crc8 = 0
		search_direction = 0
		#if LastDevice Flag = 0 then we need to init the search
		if self.LastDeviceFlag==0:
			print "LDF = 0"
			if self.wireReset()==0:
				print "WireReset=0"
				self.LastDiscrepancy = 0
				self.LastDeviceFlag = False
				self.LastFamilyDiscrepancy = 0
				return False
			self.wireWriteByte(self.WIRE_COMMAND_SEARCH(), False)
			time.sleep(.6)
			while True:


				print "Rom Byte Number is ", str(rom_byte_number), " Rom Byte Mask ", str(rom_byte_mask)
				
				buffer = 0x80 if search_direction else 0x00
				self.bus.write_byte_data(self.address, self.DS2482_COMMAND_TRIPLET(), buffer)
				byte = self.waitOnBusy()
				id_bit = (byte & 0b00100000) >> 5
				cmp_id_bit = (byte & 0b01000000) >> 6
				if (id_bit==1) and (cmp_id_bit==1):
					print "Both ID and CMP = 1"
					break
				else:
					if (id_bit != cmp_id_bit):
						print "id != cmp"
						search_direction = id_bit
					else:
						if (id_bit_number < self.LastDiscrepancy):
							search_direction = ((self.ROM_NO[rom_byte_number] & rom_byte_mask ) > 0 )
						else:
							search_direction = (id_bit_number == self.LastDiscrepancy)
						if search_direction == 0:
							last_zero = id_bit_number
							if last_zero < 9:
								self.LastFamilyDiscrepancy = last_zero
					if search_direction == 1:
						print "SD rom number ", str(rom_byte_number), " rom byte mask ", str(rom_byte_mask)
						print "Orig is ", self.ROM_NO[rom_byte_number], " result is ", hex(self.ROM_NO[rom_byte_number] | rom_byte_mask) 
						self.ROM_NO[rom_byte_number] |= rom_byte_mask
					else:
						print "SD0 rom number ", str(rom_byte_number), "rom byte mask ", str(rom_byte_mask)
						print "orig is ", self.ROM_NO[rom_byte_number], " result is ", hex(self.ROM_NO[rom_byte_number] & ~rom_byte_mask)
						self.ROM_NO[rom_byte_number] &= ~rom_byte_mask
					
					id_bit_number += 1
					rom_byte_mask <<=1
					if rom_byte_mask > 128:
						rom_byte_mask=0
					if rom_byte_mask==0:
						self.docrc8(self.ROM_NO[rom_byte_number])
						rom_byte_number += 1
						rom_byte_mask = 1
				if rom_byte_number > 7:
					break
		if (not((id_bit_number < 65)  or (self.crc8 != 0))):
			self.LastDiscrepancy = last_zero
			if (self.LastDiscrepancy == 0):
				self.LastDeviceFlag = True
			search_result = True
		if (search_result==0 or self.ROM_NO[0]==0):
			self.LastDiscrepancy = 0
			self.LastDeviceFlag = False
			self.LastFamilyDiscrepancy = 0
			search_result = False

		return search_result
	def docrc8(self, value):
		dscrc_table = [0, 94,188,226, 97, 63,221,131,194,156,126, 32,163,253, 31, 65, 157,195, 33,127,252,162, 64, 30, 95,  1,227,189, 62, 96,130,220,35,125,159,193, 66, 28,254,160,225,191, 93,  3,128,222, 60, 98,190,224,  2, 92,223,129, 99, 61,124, 34,192,158, 29, 67,161,255,70, 24,250,164, 39,121,155,197,132,218, 56,102,229,187, 89,  7,219,133,103, 57,186,228,  6, 88, 25, 71,165,251,120, 38,196,154,101, 59,217,135,  4, 90,184,230,167,249, 27, 69,198,152,122, 36,248,166, 68, 26,153,199, 37,123, 58,100,134,216, 91,  5,231,185,140,210, 48,110,237,179, 81, 15, 78, 16,242,172, 47,113,147,205,17, 79,173,243,112, 46,204,146,211,141,111, 49,178,236, 14, 80,175,241, 19, 77,206,144,114, 44,109, 51,209,143, 12, 82,176,238,50,108,142,208, 83, 13,239,177,240,174, 76, 18,145,207, 45,115,202,148,118, 40,171,245, 23, 73,  8, 86,180,234,105, 55,213,139,87,  9,235,181, 54,104,138,212,149,203, 41,119,244,170, 72, 22,233,183, 85, 11,136,214, 52,106, 43,117,151,201, 74, 20,246,168,116, 42,200,150, 21, 75,169,247,182,232, 10, 84,215,137,107, 53]	
		print "CRC8 is ", str(self.crc8), " Value is ", value
		self.crc8 = dscrc_table[self.crc8 ^ value]
		return self.crc8 


	def search(self):
		print "Searching"
		cnt = 0
		rslt = self.OWFirst()
		print "Result is "
		print rslt
		while rslt:
			print "In While Loop"
			print cnt, " Addr ", hex(self.ROM_NO[7]), ":", hex(self.ROM_NO[6]), ":", hex(self.ROM_NO[5]), ":", hex(self.ROM_NO[4]), ":", hex(self.ROM_NO[3]), ":", hex(self.ROM_NO[2]), ":", hex(self.ROM_NO[1]), ":", hex(self.ROM_NO[0])
			rslt = self.OWNext()
		return cnt
	address = 0x18
	LastDiscrepancy = 0
	LastDeviceFlag = False
	LastFamilyDiscrepancy = 0
	mAddress = 0x00
	mError = 0x00
	crc8 = 0x00
	searchAddress = [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00]
	ROM_NO = [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00]
	searchLastDiscrepancy = 0
	searchLastDeviceFlag = False


	
	def __init__(self, object):
		self.address = object
		self.bus = smbus.SMBus(1)
		self.writeConfig(0b11100001)
		config = self.readConfig()
		print "Config is"
		print bin(config)
		byte = self.bus.read_byte(self.address)
		byte = self.bus.read_byte(self.address)

class DS18B20(OW):
	
	def setResolution (self, rom, resolution):
		if (resolution == 9):
			config_register = 0b00011111
		elif (resolution ==10):
			config_register = 0b00111111
		elif (resolution == 11):
			config_register = 0b01011111
		elif (resolution == 12):
			config_register = 0b01111111
		else:
			config_register = 0b00011111
		scratchpad = [0x00,0x00,0x00,0x00, 0x00,0x00,0x00,0x00, 0x00,0x00]
		scratchpad = self.readScratchPad(rom)
		scratchpad[4] = config_register
		self.selectROM(rom)	
		self.wireWriteByte(self.DS18B20_WRITE_SCRATCHPAD(), False)
		

		for i in range (2, 5):
			self.wireWriteByte(scratchpad[i], False)
		self.wireReset()
	
	def readScratchPad(self, rom):
		self.selectROM(rom)
		self.wireWriteByte(self.DS18B20_READ_SCRATCHPAD(), False)
		scratchpad = [0x00,0x00,0x00,0x00,0x00, 0x00,0x00,0x00,0x00,0x00]
		for i in range (0, 9):
			scratchpad[i] = self.wireReadByte()
			print "Scratchpad[",i,"]=",bin(scratchpad[i])
		return scratchpad
	
#	def readScratchPad(self, rom, length):
#		self.selectROM(rom)
#		wireWriteByte(self.DS18B20_READ_SCRATCHPAD(), False)
#		for i in range (0, length):
#			scratchpad[i] = self.wireReadByte()
#		return scratchpad

	def selectROM(self, rom):
		self.wireReset()
		self.wireWriteByte(self.OW_MATCH_ROM(), False)
		time.sleep(.62)
		for i in range (0, 8):
			self.wireWriteByte(rom[i], False)
			self.waitOnBusy()

	def skipROM(self):
		self.wireReset()
		self.wireWriteByte(self.OW_SKIP_ROM(), False)
		time.sleep(.62)

	def readROM(self, rom):
		self.wireReset()
		self.wireWriteByte(self.OW_READ_ROM(), False)
		time.sleep(.62)
	def startConversion(self):
		self.skipROM()
		self.wireWriteByte(self.DS18B20_CONVERT(), False)
	def startConversion(self, rom):
		self.selectROM(rom)
		self.wireWriteByte(self.DS18B20_CONVERT(), False)
	def getTempF(self, rom):
		scratchpad = [0x00,0x00,0x00,0x00,0x00, 0x00,0x00,0x00,0x00,0x00]
		scratchpad = self.readScratchPad(rom)
		print "Scratchpad[1]=", bin(scratchpad[1]<<8), " Scratchpad[0]=", bin(scratchpad[0])
		print "Int S1=", int(scratchpad[1]<<8), " S2=", int(scratchpad[0])
		rawtemp = ((scratchpad[1]&0xFF)<<8 | (scratchpad[0]&0xFF))*.0625
		if (scratchpad[1] & 0x80):
			temp = -(~(rawtemp-1)/16)
		else:
			temp = rawtemp / 16
		return (rawtemp *1.8)+32

			
		
		
	


print "test"
#x = OW(0x18)
#print (x.getAddress())
#x.readStatus()
#print x.readConfig()
#x.search(y)
y = DS18B20(0x18)
y.search()
print y.ROM_NO
print "[",hex(y.ROM_NO[0]), "," ,hex(y.ROM_NO[1]), "," ,hex(y.ROM_NO[2]), "," ,hex(y.ROM_NO[3]), "," ,hex(y.ROM_NO[4]), "," ,hex(y.ROM_NO[5]), "," ,hex(y.ROM_NO[6]),",",hex(y.ROM_NO[7])
rom=[ 0x28 , 0x5 , 0x3e , 0x1 , 0x8 , 0x0 , 0x0 , 0x79 ]
y.startConversion(rom)
time.sleep(.650)
print y.getTempF(rom)
print "The End"
