
#include "mac_link.h"
#include "HFC_debug.h"

int8_t MACLink::activateAsTarget(uint16_t timeout)
{
	HFC.begin();
	HFC.SAMConfig();
    return HFC.tgInitAsTarget(timeout);
}

bool MACLink::write(const uint8_t *header, uint8_t hlen, const uint8_t *body, uint8_t blen)
{
    return HFC.tgSetData(header, hlen, body, blen);
}

int16_t MACLink::read(uint8_t *buf, uint8_t len)
{
    return HFC.tgGetData(buf, len);
}
