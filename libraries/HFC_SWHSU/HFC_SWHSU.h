
#ifndef __HFC_SWHSU_H__
#define __HFC_SWHSU_H__

#include <SoftwareSerial.h>

#include "HFCInterface.h"
#include "Arduino.h"

#define HFC_SWHSU_DEBUG

#define HFC_SWHSU_READ_TIMEOUT						(1000)

class HFC_SWHSU : public HFCInterface {
public:
    HFC_SWHSU(SoftwareSerial &serial);
    
    void begin();
    void wakeup();
    virtual int8_t writeCommand(const uint8_t *header, uint8_t hlen, const uint8_t *body = 0, uint8_t blen = 0);
    int16_t readResponse(uint8_t buf[], uint8_t len, uint16_t timeout);
    
private:
    SoftwareSerial* _serial;
    uint8_t command;
    
    int8_t readAckFrame();
    
    int8_t receive(uint8_t *buf, int len, uint16_t timeout=HFC_SWHSU_READ_TIMEOUT);
};

#endif
