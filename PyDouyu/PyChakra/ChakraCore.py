

# import lib
import ctypes 
import os


_g_script_path = os.path.split(os.path.realpath(__file__))[0]
_g_dll_path = _g_script_path + "\\" + "ChakraCore.dll"
# ----------------------------------------------------------------
# Chakra
# typedef void *JsRef;
# typedef JsRef JsValueRef;
# ----------------------------------------------------------------

class _g_Chakra_Static_:
	ctxCount = 0 # Access through class	
	ChakraCore = ctypes.WinDLL(_g_dll_path)
	
def ChakraGetExceptionInfo(Chakra):
	ChakraCore = _g_Chakra_Static_.ChakraCore
	Exception = Chakra.Exception
	return ChakraConvertVal2String(Exception)

def ChakraConvertVal2String(JsValueRef):
	ChakraCore = _g_Chakra_Static_.ChakraCore
	JSString = ctypes.c_void_p()	
	if ChakraCore.JsConvertValueToString(JsValueRef,ctypes.pointer(JSString)) != 0:
		return None
	lenJsString =  ctypes.c_int(0)
	ChakraCore.JsCopyString(JSString,0,0,ctypes.pointer(lenJsString))
	if lenJsString.value > 0:
		strbuf = ctypes.create_string_buffer(lenJsString.value +1)
		if ChakraCore.JsCopyString(JSString,ctypes.pointer(strbuf),lenJsString.value+1,ctypes.pointer(lenJsString)) ==0:
			return strbuf.value.decode(encoding="utf-8")
	return None

class Chakra():
	def __init__(self):
		ChakraCore = _g_Chakra_Static_.ChakraCore
		_g_Chakra_Static_.ctxCount +=1
		self.jsrt = ctypes.c_void_p()
		self.context= ctypes.c_void_p()
		self.result = ctypes.c_void_p()		
		self.currentSourceContext = ctypes.c_int(_g_Chakra_Static_.ctxCount) 
		self.sourceUrl = ctypes.c_wchar_p("")
		self.Status = 0
		self.ErrorMsg = ""
		self.Exception = ctypes.c_void_p()		
		
		self.Status = ChakraCore.JsCreateRuntime(ctypes.c_int(0),ctypes.c_void_p(0),ctypes.pointer(self.jsrt)) 
		if self.Status!= 0:
			self.ErrorMsg = "CreateRuntime Failed"
			return None
		 
		self.Status = ChakraCore.JsCreateContext(self.jsrt,ctypes.pointer(self.context))
		if self.Status!= 0:
			self.ErrorMsg = "CreateContext Failed"
			return None
			
		self.Status = ChakraCore.JsSetCurrentContext(self.context);
		if self.Status!= 0:
			self.ErrorMsg = "SetCurrentContext Failed"
			return None
				
	def RunScript(self,scripttxt):
		ChakraCore = _g_Chakra_Static_.ChakraCore
		self.Status = ChakraCore.JsRunScript(ctypes.c_wchar_p(scripttxt), self.currentSourceContext,self.sourceUrl, ctypes.pointer(self.result))
		if self.Status!= 0:
			self.ErrorMsg = "RunScript Failed"
			ChakraCore.JsGetAndClearException(ctypes.pointer(self.Exception))
			return None
		return ChakraConvertVal2String(self.result)
			
	def Dispose(self):
		ChakraCore = _g_Chakra_Static_.ChakraCore
		ChakraCore.JsSetCurrentContext(0)
		ChakraCore.JsDisposeRuntime(self.jsrt)
		
		
if __name__ == "__main__":
	strScript ='(()=>{ return "Hello Chakra !!" })();'
	ctx = Chakra()
	jsResult = ctx.RunScript(strScript)
	if jsResult == None:
		print(ChakraGetExceptionInfo(ctx))
		exit()
	print(jsResult)
	ctx.Dispose()
	
		
		
		