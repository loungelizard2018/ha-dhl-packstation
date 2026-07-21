from dataclasses import dataclass
from typing import Any
from aiohttp import ClientError, ClientSession
from yarl import URL
from .const import API_BASE_URL,API_PATH
class DHLError(Exception): pass
class DHLAuthError(DHLError): pass
class DHLNotFoundError(DHLError): pass
class DHLConnectionError(DHLError): pass
class DHLResponseError(DHLError): pass
@dataclass(frozen=True,slots=True)
class PackstationData:
 location_id:str; station_number:str; station_name:str; display_name:str; street:str; postal_code:str; city:str; country_code:str; contained_in_place:str|None; latitude:float|None; longitude:float|None; weekly_forecast:dict[str,str]; raw:dict[str,Any]
 def capacity_for_weekday(self,weekday:str)->str: return self.weekly_forecast.get(weekday,"unknown")
class DHLPackstationApiClient:
 def __init__(self,session:ClientSession,api_key:str): self._session=session; self._api_key=api_key
 async def async_get_station(self,*,country_code:str,postal_code:str,station_number:str,display_name:str|None=None)->PackstationData:
  try:
   async with self._session.get(URL(API_BASE_URL).with_path(API_PATH),params={"keywordId":station_number,"countryCode":country_code,"postalCode":postal_code},headers={"DHL-API-Key":self._api_key,"Accept":"application/json"},timeout=20) as r:
    if r.status in (401,403): raise DHLAuthError
    if r.status==404: raise DHLNotFoundError
    r.raise_for_status(); p=await r.json(content_type=None)
  except DHLError: raise
  except (ClientError,TimeoutError,ValueError) as e: raise DHLConnectionError(str(e)) from e
  if not isinstance(p,dict): raise DHLResponseError
  loc=p.get("location") or {}; ids=loc.get("ids") or []; lid=next((x.get("locationId") for x in ids if x.get("provider")=="parcel"),None) or next((x.get("locationId") for x in ids if x.get("locationId")),None)
  if not lid: raise DHLResponseError
  place=p.get("place") or {}; a=place.get("address") or {}; g=place.get("geo") or {}; c=place.get("containedInPlace") or {}; forecast={}
  for x in p.get("averageCapacityDayOfWeek") or []:
   if isinstance(x.get("dayOfWeek"),str) and isinstance(x.get("capacity"),str): forecast[x["dayOfWeek"].rsplit("/",1)[-1]]=x["capacity"]
  def f(v):
   try:return float(v)
   except:return None
  name=str(p.get("name") or f"Packstation {station_number}")
  return PackstationData(str(lid),str(loc.get("keywordId") or station_number),name,display_name or name,str(a.get("streetAddress") or ""),str(a.get("postalCode") or postal_code),str(a.get("addressLocality") or ""),str(a.get("countryCode") or country_code),str(c.get("name")) if c.get("name") else None,f(g.get("latitude")),f(g.get("longitude")),forecast,p)
