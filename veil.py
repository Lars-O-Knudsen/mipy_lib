


import random, esp32, ucryptolib, json, binascii



VEIL_CONTENT_LEN_KEY = "__contentlen__"
VEIL_CONTENT_KEY = "__content__"

class Veil:

    def __init__(self, namespace: str, force_init: bool = False):
        self._ns = esp32.NVS(namespace)
        self._content = self.__fetch_object(force_init)


    def set_value(self, key: str, value: str) -> None:
        enc = self.__get_encryptor()
        crpt = enc.encrypt(value + (chr(0) * ((16 - (len(value) % 16)) % 16)))
        self.__put_value_hex(key, crpt)


    def get_value(self, key: str) -> str:
        dcr = self.__get_decryptor()
        value = dcr.decrypt(self.__get_value_hex(key))
        return value.rstrip(b'\x00')


    def save(self) -> None:
        self.__store_object()


    def __put_value_hex(self, key, val) -> None:
        hx = binascii.hexlify(val)
        self._content[key] = hx


    def __get_value_hex(self, key) -> any:
        hx = self._content[key]
        return binascii.unhexlify(hx)


    def __store_object(self) -> None:
        s = json.dumps(self._content)
        self._ns.set_i32(VEIL_CONTENT_LEN_KEY, len(s))
        self._ns.set_blob(VEIL_CONTENT_KEY, s)
        self._ns.commit()


    def __fetch_object(self, force_init: bool = False) -> dict:
        if force_init: return self.__init_content()
        try:
            content_len = self._ns.get_i32(VEIL_CONTENT_LEN_KEY)
        except:
            return self.__init_content()
        buf = bytearray(content_len)
        act_len = self._ns.get_blob(VEIL_CONTENT_KEY, buf)
        return json.loads(buf[:act_len])


    def __init_content(self):
        random.seed()
        self._content = {}
        secret = "".join([chr(random.randint(65, 123)) for x in range(16)])
        self.__put_value_hex("__secret__", secret)

        iv = bytearray([random.randint(65, 123) for x in range(16)])
        self.__put_value_hex("__iv__", iv)
        return self._content

    def __get_encryptor(self) -> any:
        secret = self.__get_value_hex('__secret__')
        iv = self.__get_value_hex('__iv__')
        return ucryptolib.aes(secret, 2, iv)


    def __get_decryptor(self) -> any:
        secret = self.__get_value_hex('__secret__')
        iv = self.__get_value_hex('__iv__')
        return ucryptolib.aes(secret, 2, iv)

