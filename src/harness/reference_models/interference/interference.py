#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

"""
==================================================================================
  Compute Interference caused by a grant for all the incumbent types
  APIs in this file are used by IAP and Aggregate Interference Reference Models

  The main routines are:
   
    computeInterference
    computeInterferencePpaGwpzPoint 
    computeInterferenceEsc 
    computeInterferenceFssCochannel 
    computeInterferenceFssBlocking 
    getEffectiveSystemEirp 

  The common utility APIs are:
    
    getGrantObjectsFromFAD
    getAllGrantInformationFromCbsdDataDump 
    findOverlappingGrantsInsideNeighborhood
    getProtectedChannels

  The routines return a interference caused by a grant in the neighborhood of 
  FSS/GWPZ/PPA/ESC incumbent types
==================================================================================
"""
import numpy as np
from reference_models.antenna import antenna
from reference_models.geo import vincenty
from reference_models.propagation import wf_itm
from reference_models.propagation import wf_hybrid
from collections import namedtuple
from enum import Enum

# Initialize terrain driver
# terrainDriver = terrain.TerrainDriver()
terrainDriver = wf_itm.terrainDriver

# Set constant parameters based on requirements in the WINNF-TS-0112
# [R2-SGN-16]
GWPZ_NEIGHBORHOOD_DIST = 40  # neighborhood distance from a CBSD to a given protection
# point (in km) in GWPZ protection area
PPA_NEIGHBORHOOD_DIST = 40  # neighborhood distance from a CBSD to a given protection
# point (in km) in PPA protection area

FSS_CO_CHANNEL_NEIGHBORHOOD_DIST = 150  # neighborhood distance from a CBSD to FSS for
# co-channel protection

FSS_BLOCKING_NEIGHBORHOOD_DIST = 40  # neighborhood distance from a CBSD to FSS
# blocking protection

ESC_NEIGHBORHOOD_DIST_A = 40  # neighborhood distance from a ESC to category A CBSD

ESC_NEIGHBORHOOD_DIST_B = 80  # neighborhood distance from a ESC to category B CBSD


# Frequency used in propagation model (in MHz) [R2-SGN-04]
FREQ_PROP_MODEL_MHZ = 3625.0

# CBRS Band Frequency Range (Hz)
CBRS_LOW_FREQ_HZ = 3550.e6
CBRS_HIGH_FREQ_HZ = 3700.e6

# FSS Passband low frequency range  (Hz)
FSS_LOW_FREQ_HZ = 3600.e6

# FSS Passband for TT&C (Hz)
FSS_TTC_LOW_FREQ_HZ = 3700.e6
FSS_TTC_HIGH_FREQ_HZ = 4200.e6

# ESC IAP for Out-of-Band Category A CBSDs in Frequency Range (Hz)
ESC_CAT_A_LOW_FREQ_HZ = 3550.e6
ESC_CAT_A_HIGH_FREQ_HZ = 3660.e6

# ESC Passband Frequency Range (Hz)
ESC_LOW_FREQ_HZ = 3550.e6
ESC_HIGH_FREQ_HZ = 3680.e6

# ESC Channel 21 Center Frequency
ESC_CH21_CF_HZ = 36525.e5

# One Mega Hertz
MHZ = 1.e6

# Channel bandwidth over which SASs execute the IAP process
IAPBW_HZ = 5.e6

# GWPZ Area Protection reference bandwidth for the IAP process
GWPZ_RBW_HZ = 10.e6

# PPA Area Protection reference bandwidth for the IAP process
PPA_RBW_HZ = 10.e6

# GWPZ and PPA height (m)
GWPZ_PPA_HEIGHT = 1.5

# In-band insertion loss
IN_BAND_INSERTION_LOSS = 0.5

# Define an enumeration class named ProtectedEntityType with members
# 'GWPZ_AREA', 'PPA_AREA', 'FSS_CO_CHANNEL', 'FSS_BLOCKING', 'ESC'


class ProtectedEntityType(Enum):
  GWPZ_AREA = 1
  PPA_AREA = 2
  FSS_CO_CHANNEL = 3
  FSS_BLOCKING = 4
  ESC = 5

# Global container to store neighborhood distance type of all the protection 
_DISTANCE_PER_PROTECTION_TYPE = {
   ProtectedEntityType.GWPZ_AREA :  (GWPZ_NEIGHBORHOOD_DIST, GWPZ_NEIGHBORHOOD_DIST),
   ProtectedEntityType.PPA_AREA : ( PPA_NEIGHBORHOOD_DIST,  PPA_NEIGHBORHOOD_DIST),
   ProtectedEntityType.FSS_CO_CHANNEL : ( FSS_CO_CHANNEL_NEIGHBORHOOD_DIST,  FSS_CO_CHANNEL_NEIGHBORHOOD_DIST),
   ProtectedEntityType.FSS_BLOCKING : ( FSS_BLOCKING_NEIGHBORHOOD_DIST,  FSS_BLOCKING_NEIGHBORHOOD_DIST),
   ProtectedEntityType.ESC: (ESC_NEIGHBORHOOD_DIST_A, ESC_NEIGHBORHOOD_DIST_B)
    }

# Define CBSD grant, i.e., a tuple with named fields of 'latitude',
# 'longitude', 'height_agl', 'indoor_deployment', 'antenna_azimuth',
# 'antenna_gain', 'antenna_beamwidth', 'cbsd_category', 
# 'max_eirp', 'low_frequency', 'high_frequency', 'is_managed_grant'
CbsdGrantInformation = namedtuple('CbsdGrantInformation',
                       ['latitude', 'longitude', 'height_agl', 
                        'indoor_deployment', 'antenna_azimuth', 'antenna_gain',
                        'antenna_beamwidth', 'cbsd_category', 
                        'max_eirp', 'low_frequency', 'high_frequency', 
                        'is_managed_grant'])

# Define protection constraint, i.e., a tuple with named fields of
# 'latitude', 'longitude', 'low_frequency', 'high_frequency'
ProtectionConstraint = namedtuple('ProtectionConstraint',
                                  ['latitude', 'longitude', 'low_frequency',
                                   'high_frequency', 'entity_type'])

# Define FSS Protection Point, i.e., a tuple with named fields of
# 'latitude', 'longitude', 'height_agl', 'max_gain_dbi', 'pointing_azimuth',
# 'pointing_elevation' 
FssProtectionPoint = namedtuple('FssProtectionPoint',
                                   ['latitude', 'longitude',
                                    'height_agl', 'max_gain_dbi',
                                    'pointing_azimuth', 'pointing_elevation'])


# Define ESC information, i.e., a tuple with named fields of
# 'antenna_height', 'antenna_azimuth', 'antenna_gain', 'antenna_pattern_gain'
EscInformation = namedtuple('EscInformation',
                                 ['antenna_height', 'antenna_azimuth',
                                  'antenna_gain', 'antenna_pattern_gain'])

def dbToLinear(x):
  """This function returns dBm to mW converted value"""
  return 10**(x / 10)

def linearToDb(x):
  """This function returns mW to dBm converted value"""
  return 10 * np.log10(x)

def getProtectedChannels(low_freq_hz, high_freq_hz):
  """Gets protected channels list 

  Performs 5MHz IAP channelization and returns a list of tuple containing 
  (low_freq,high_freq)

  Args:
    low_freq_hz: Low frequency of the protected entity(Hz).
    high_freq_hz: High frequency of the protected entity(Hz)
  Returns:
    An array of protected channel frequency range tuple 
    (low_freq_hz,high_freq_hz). 
  """
  assert low_freq_hz < high_freq_hz, 'Low frequency is greater than high frequency'

  channels = np.arange( max(low_freq_hz, 3550*MHZ), min(high_freq_hz, 3700*MHZ), 5*MHZ)

  return [(low, high) for low,high in zip(channels, channels+5*MHZ)]


def findGrantsInsideNeighborhood(grants, protection_point, entity_type):
  """Finds grants inside protection entity neighborhood

  Args:
    grants: a list of grants of type GAA
    protection_point: tuple containing (latitude,longitude) of a protection entity 
    entity_type: enum of type ProtectedEntityType 
  Returns:
    grants_inside: a list of grants, each one being a namedtuple of type
                   CbsdGrantInformation, of all CBSDs inside the neighborhood 
                   of the protection constraint.
  """
  # Initialize an empty list
  grants_inside = []

  # Loop over each CBSD grant
  for grant in grants:
    # Compute distance from CBSD location to protection constraint location
    dist_km, _, _ = vincenty.GeodesicDistanceBearing(grant.latitude, 
                      grant.longitude, protection_point[0], protection_point[1])

    # Check if CBSD is inside the neighborhood of protection constraint
    if dist_km <= _DISTANCE_PER_PROTECTION_TYPE[entity_type][grant.cbsd_category == 'B']:
      grants_inside.append(grant)

  return grants_inside


def findOverlappingGrants(grants, constraint):
  """Finds grants inside protection entity neighborhood
   
  Grants overlapping with frequency range of the protection entity are 
  considered as overlapping grants 

  Args:
    grants: a list of grants of type GAA
    constraint: protection constraint of type ProtectionConstraint
  Returns:
    grants_inside: a list of grants, each one being a namedtuple of type
                   CbsdGrantInformation, of all CBSDs inside the neighborhood 
                   of the protection constraint.
  """

  # Initialize an empty list
  grants_inside = []

  # Loop over each CBSD grant
  for grant in grants:
    # Check frequency range
    overlapping_bw = min(grant.high_frequency, constraint.high_frequency) \
                        - max(grant.low_frequency, constraint.low_frequency)
    freq_check = (overlapping_bw > 0)
    
    # ESC Passband is 3550-3680MHz
    # Category A CBSD grants are considered in the neighborhood only for 
    # constraint frequency range 3550-3660MHz
    if ProtectedEntityType.ESC == _DISTANCE_PER_PROTECTION_TYPE[constraint.entity_type]:
      if grant.cbsd_category == 'A' and constraint.high_frequency > ESC_CAT_A_HIGH_FREQ_HZ:
        freq_check = False

    # Append the grants information if it is inside the neighborhood of
    # protection constraint
    if freq_check:
      grants_inside.append(grant)

  return grants_inside


def getGrantObjectsFromFAD(sas_uut_fad_object, sas_th_fad_objects):
  """Extracts CBSD grant objects from FAD object

  Args:
    sas_uut_fad_object: FAD object from SAS UUT
    sas_th_fad_object: a list of FAD objects from SAS Test Harness
  Returns:
    grant_objects: a list of CBSD grants dictionary containing registrationRequest
    and grants
  """
  # List of CBSD grant tuples extracted from FAD record
  grant_objects = []

  # Creating list of cbsds
  cbsd_list_uut = []
  cbsd_list_th = []

  for cbsds in sas_uut_fad_object.getCbsdRecords():
    cbsd_list_uut.append(cbsds)

  grant_objects_uut = getAllGrantInformationFromCbsdDataDump(cbsd_list_uut, True)

  for fad in sas_th_fad_objects:
    for cbsds in fad.getCbsdRecords():
      cbsd_list_th.append(cbsds)
      grant_objects_test_harness = getAllGrantInformationFromCbsdDataDump(
                                     cbsd_list_th, False)

  grant_objects = grant_objects_uut + grant_objects_test_harness

  return grant_objects 

def getAllGrantInformationFromCbsdDataDump(cbsd_data_records, is_managing_sas=True):
  """Extracts list of CbsdGrantInformation namedtuple

  Routine to extract CbsdGrantInformation tuple from CBSD data records from 
  FAD objects

  Args:
    cbsd_data_records: A list CbsdData object retrieved from FAD records.
    is_managing_sas: flag indicating cbsd data record is from managing SAS or 
                     peer SAS
                     True - Managing SAS, False - Peer SAS
  Returns:
    grant_objects: a list of grants, each one being a namedtuple of type 
                   CBSDGrantInformation, of all CBSDs from SAS UUT FAD and 
                   SAS Test Harness FAD
  """

  grant_objects = []

  # Loop over each CBSD grant
  for cbsd_data_record in cbsd_data_records:
    registration = cbsd_data_record.get('registrationRequest')
    grants = cbsd_data_record.get('grants')

    # Check CBSD location
    lat_cbsd = registration.get('installationParam', {}).get('latitude')
    lon_cbsd = registration.get('installationParam', {}).get('longitude')
    height_cbsd = registration.get('installationParam', {}).get('height')
    height_type_cbsd = registration.get('installationParam', {}).get('heightType')
    if height_type_cbsd == 'AMSL':
      altitude_cbsd = terrainDriver.GetTerrainElevation(lat_cbsd, lon_cbsd)
      height_cbsd = height_cbsd - altitude_cbsd

    # Sanity check on CBSD antenna height
    if height_cbsd < 1 or height_cbsd > 1000:
      raise ValueError('CBSD height is less than 1m or greater than 1000m.')

    for grant in grants:
      # Return CBSD information
      cbsd_grant = CbsdGrantInformation(
        # Get information from the registration
        latitude=lat_cbsd,
        longitude=lon_cbsd,
        height_agl=height_cbsd,
        indoor_deployment=registration.get('installationParam', {})
                                      .get('indoorDeployment'),
        antenna_azimuth=registration.get('installationParam', {})
                                    .get('antennaAzimuth'),
        antenna_gain=registration.get('installationParam', {})
                                 .get('antennaGain'),
        antenna_beamwidth=registration.get('installationParam', {})
                                      .get('antennaBeamwidth'),
        cbsd_category=registration.get('cbsdCategory'),
        max_eirp=grant.get('operationParam', {}).get('maxEirp'),
        low_frequency=grant.get('operationParam', {})
                        .get('operationFrequencyRange', {})
                        .get('lowFrequency'),
        high_frequency=grant.get('operationParam', {})
                         .get('operationFrequencyRange', {})
                         .get('highFrequency'),
        is_managed_grant=is_managing_sas)
      grant_objects.append(cbsd_grant)
  return grant_objects

def computeInterferencePpaGwpzPoint(cbsd_grant, constraint, h_inc_ant, 
                                  max_eirp, region='SUBURBAN'):
  """Compute interference grant causes to GWPZ or PPA protection area
  
  Routine to compute interference neighborhood grant causes to protection 
  point within GWPZ or PPA protection area

  Args:
    cbsd_grant: a namedtuple of type CbsdGrantInformation
    constraint: protection constraint of type ProtectionConstraint
    h_inc_ant: reference incumbent antenna height (in meters)
    max_eirp: The maximum EIRP allocated to the grant during IAP procedure
    region: Region type of the GWPZ or PPA area
  Returns:
    interference: interference contribution(dBm)
  """

  if (cbsd_grant.latitude == constraint.latitude) and \
    (cbsd_grant.longitude == constraint.longitude): 
    db_loss = 0
    incidence_angles = wf_itm._IncidenceAngles(hor_cbsd=0, ver_cbsd=0, hor_rx=0, ver_rx=0)
  else:
    # Get the propagation loss and incident angles for area entity 
    db_loss, incidence_angles, _ = wf_hybrid.CalcHybridPropagationLoss(
                                     cbsd_grant.latitude, cbsd_grant.longitude,
                                     cbsd_grant.height_agl, constraint.latitude,
                                     constraint.longitude, h_inc_ant,
                                     cbsd_grant.indoor_deployment,
                                     reliability=-1, 
                                     freq_mhz=FREQ_PROP_MODEL_MHZ,
                                     region=region)

  # Compute CBSD antenna gain in the direction of protection point
  ant_gain = antenna.GetStandardAntennaGains(incidence_angles.hor_cbsd,
               cbsd_grant.antenna_azimuth, cbsd_grant.antenna_beamwidth,
               cbsd_grant.antenna_gain)

  # Get the interference value for area entity
  eirp = getEffectiveSystemEirp(max_eirp, cbsd_grant.antenna_gain,
                   ant_gain)

  interference = eirp - db_loss
  return interference


def computeInterferenceEsc(cbsd_grant, constraint, esc_antenna_info, max_eirp):
  """Compute interference grant causes to a ESC protection point
  
  Routine to compute interference neighborhood grant causes to ESC protection 
  point

  Args:
    cbsd_grant: a namedtuple of type CbsdGrantInformation
    constraint: protection constraint of type ProtectionConstraint
    esc_antenna_info: contains information on ESC antenna height, azimuth,
                      gain and pattern gain
    max_eirp: The maximum EIRP allocated to the grant during IAP procedure
  Returns:
    interference: interference contribution(dBm)
  """

  # Get the propagation loss and incident angles for ESC entity
  db_loss, incidence_angles, _ = wf_itm.CalcItmPropagationLoss(cbsd_grant.latitude, 
                                   cbsd_grant.longitude, cbsd_grant.height_agl, 
                                   constraint.latitude, constraint.longitude, 
                                   esc_antenna_info.antenna_height,
                                   cbsd_grant.indoor_deployment, reliability=-1,
                                   freq_mhz=FREQ_PROP_MODEL_MHZ)

  # Compute CBSD antenna gain in the direction of protection point
  ant_gain = antenna.GetStandardAntennaGains(incidence_angles.hor_cbsd,
               cbsd_grant.antenna_azimuth, cbsd_grant.antenna_beamwidth,
               cbsd_grant.antenna_gain)

  # Compute ESC antenna gain in the direction of CBSD
  esc_ant_gain = antenna.GetAntennaPatternGains(incidence_angles.hor_rx,
                   esc_antenna_info.antenna_azimuth, 
                   esc_antenna_info.antenna_pattern_gain,
                   esc_antenna_info.antenna_gain)

  # Get the total antenna gain by summing the antenna gains from CBSD to ESC
  # and ESC to CBSD
  effective_ant_gain = ant_gain + esc_ant_gain

  # Compute the interference value for ESC entity
  eirp = getEffectiveSystemEirp(max_eirp, cbsd_grant.antenna_gain,effective_ant_gain)

  interference = eirp - db_loss - IN_BAND_INSERTION_LOSS
  return interference


def computeInterferenceFssCochannel(cbsd_grant, constraint, fss_info, max_eirp):
  """Compute interference grant causes to a FSS protection point
  
  Routine to compute interference neighborhood grant causes to FSS protection 
  point for co-channel passband
  Args:
    cbsd_grant: a namedtuple of type CbsdGrantInformation
    constraint: protection constraint of type ProtectionConstraint
    fss_info: contains information on antenna height the tangent 
              and perpendicular components.
    max_eirp: The maximum EIRP allocated to the grant during IAP procedure
  Returns:
    interference: interference contribution(dBm)
  """

  # Get the propagation loss and incident angles for FSS entity_type
  db_loss, incidence_angles, _ = wf_itm.CalcItmPropagationLoss(cbsd_grant.latitude, 
                                   cbsd_grant.longitude, cbsd_grant.height_agl, 
                                   constraint.latitude, constraint.longitude, 
                                   fss_info.height_agl, cbsd_grant.indoor_deployment, 
                                   reliability=-1, freq_mhz=FREQ_PROP_MODEL_MHZ)

  # Compute CBSD antenna gain in the direction of protection point
  ant_gain = antenna.GetStandardAntennaGains(incidence_angles.hor_cbsd,
               cbsd_grant.antenna_azimuth, cbsd_grant.antenna_beamwidth,
               cbsd_grant.antenna_gain)

  # Compute FSS antenna gain in the direction of CBSD
  fss_ant_gain = antenna.GetFssAntennaGains(incidence_angles.hor_rx, 
                   incidence_angles.ver_rx, fss_info.pointing_azimuth,
                   fss_info.pointing_elevation, fss_info.max_gain_dbi)

  # Get the total antenna gain by summing the antenna gains from CBSD to FSS
  # and FSS to CBSD
  effective_ant_gain = ant_gain + fss_ant_gain

  # Compute the interference value for Fss co-channel entity
  eirp = getEffectiveSystemEirp(max_eirp, cbsd_grant.antenna_gain,
                   effective_ant_gain)
  interference = eirp - db_loss - IN_BAND_INSERTION_LOSS
  return interference


def getFssMaskLoss(cbsd_grant, constraint):
  """Gets the FSS mask loss for a FSS blocking protection constraint"""
  # Get 50MHz offset below the lower edge of the FSS earth station
  offset = constraint.low_frequency - 50.e6

  # Get CBSD grant frequency range
  cbsd_freq_range = cbsd_grant.high_frequency - cbsd_grant.low_frequency

  fss_mask_loss = 0

  # if lower edge of the FSS passband is less than CBSD grant
  # lowFrequency and highFrequency
  if constraint.low_frequency < cbsd_grant.low_frequency and\
         constraint.low_frequency < cbsd_grant.high_frequency:
    fss_mask_loss = 0.5 

  # if CBSD grant lowFrequency and highFrequency is less than
  # 50MHz offset from the FSS passband lower edge
  elif cbsd_grant.low_frequency < offset and\
     cbsd_grant.high_frequency < offset:
    fss_mask_loss = linearToDb((cbsd_freq_range / MHZ) * 0.25)

  # if CBSD grant lowFrequency is less than 50MHz offset and
  # highFrequency is greater than 50MHz offset
  elif cbsd_grant.low_frequency < offset and\
            cbsd_grant.high_frequency > offset:
    low_freq_mask_loss = linearToDb(((offset - cbsd_grant.low_frequency) /
                                                     MHZ) * 0.25)
    fss_mask_loss = low_freq_mask_loss + linearToDb(((cbsd_grant.high_frequency - offset) / 
                                              MHZ) * 0.6)

  # if FSS Passband lower edge frequency is grater than CBSD grant
  # lowFrequency and highFrequency and
  # CBSD grand low and high frequencies are greater than 50MHz offset
  elif constraint.low_frequency > cbsd_grant.low_frequency and \
      constraint.low_frequency > cbsd_grant.high_frequency and \
      cbsd_grant.low_frequency > offset and\
             cbsd_grant.high_frequency > offset:
    fss_mask_loss = linearToDb((cbsd_freq_range / MHZ) * 0.6)

  return fss_mask_loss


def computeInterferenceFssBlocking(cbsd_grant, constraint, fss_info, max_eirp):
  """Compute interference grant causes to a FSS protection point
  
  Routine to compute interference neighborhood grant causes to FSS protection 
  point for blocking passband

  Args:
    cbsd_grant: a namedtuple of type CbsdGrantInformation
    constraint: protection constraint of type ProtectionConstraint
    fss_info: contains information on antenna height on 
              the tangent and perpendicular components.
    max_eirp: The maximum EIRP allocated to the grant during IAP procedure
  Returns:
    interference: interference contribution(dBm)
  """

  # Get the propagation loss and incident angles for FSS entity 
  # blocking channels
  db_loss, incidence_angles, _ = wf_itm.CalcItmPropagationLoss(
                                   cbsd_grant.latitude, cbsd_grant.longitude,
                                   cbsd_grant.height_agl, constraint.latitude,
                                   constraint.longitude, fss_info.height_agl,
                                   cbsd_grant.indoor_deployment, reliability=-1,
                                   freq_mhz=FREQ_PROP_MODEL_MHZ)

  # Compute CBSD antenna gain in the direction of protection point
  ant_gain = antenna.GetStandardAntennaGains(incidence_angles.hor_cbsd,
               cbsd_grant.antenna_azimuth, cbsd_grant.antenna_beamwidth,
               cbsd_grant.antenna_gain)

  # Compute FSS antenna gain in the direction of CBSD
  fss_ant_gain = antenna.GetFssAntennaGains(incidence_angles.hor_rx, 
                   incidence_angles.ver_rx, fss_info.pointing_azimuth, 
                   fss_info.pointing_elevation, fss_info.max_gain_dbi)


  # Get the total antenna gain by summing the antenna gains from CBSD to FSS
  # and FSS to CBSD
  effective_ant_gain = ant_gain + fss_ant_gain

  # Compute EIRP of CBSD grant inside the frequency range of 
  # protection constraint
  eirp = getEffectiveSystemEirp(max_eirp, cbsd_grant.antenna_gain, 
           effective_ant_gain, (cbsd_grant.high_frequency - cbsd_grant.low_frequency))
  # Calculate the interference contribution
  interference = eirp - getFssMaskLoss(cbsd_grant, constraint) - db_loss

  return interference


def getEffectiveSystemEirp(max_eirp, cbsd_max_ant_gain, effective_ant_gain, 
                           reference_bandwidth=IAPBW_HZ):
  """Calculates effective EIRP caused by a grant 
  
  Utility API to get effective EIRP caused by a grant in the 
  neighborhood of the protected entity FSS/ESC/PPA/GWPZ.

  Args:
    max_eirp: The maximum EIRP allocated to the grant during IAP procedure
    cbsd_max_ant_gain: The nominal antenna gain of the CBSD.
    effective_ant_gain: The actual total antenna gains at the CBSD and protected entity. 
      This takes into account the actual antenna patterns.
    reference_bandwidth: Reference bandwidth over which effective EIRP is 
                         calculated
  Returns:
    eirp_cbsd: Effective EIRP of the CBSD(dBm)
  """

  eirp_cbsd = ((max_eirp - cbsd_max_ant_gain) + effective_ant_gain + linearToDb
            (reference_bandwidth / MHZ))

  return eirp_cbsd

def computeInterference(grant, eirp, channel_constraint, fss_info=None, 
  esc_antenna_info=None, region_type=None):
  """Calculates interference caused by a grant 
  
  Utility API to get interference caused by a grant in the 
  neighborhood of the protected entity FSS/ESC/PPA/GWPZ.

  Args:
    grant : namedtuple of type CbsdGrantInformation
    eirp : EIRP of the grant 
    channel_constraint: namedtuple f type ProtectionConstraint
    fss_info: contains information on antenna height
              on the tangent and perpendicular components.
    esc_antenna_info: contains information on ESC antenna height, azimuth, 
                      gain and pattern gain 
    region_type: region type of protection PPA/GWPZ area.
  Returns:
    interference: Interference caused by a grant(dBm)
  """

  # Compute interference to FSS Co-channel protection constraint
  if channel_constraint.entity_type is ProtectedEntityType.FSS_CO_CHANNEL:
    interference = dbToLinear(computeInterferenceFssCochannel(
                     grant, channel_constraint, fss_info, eirp))

  # Compute interference to FSS Blocking protection constraint
  elif channel_constraint.entity_type is ProtectedEntityType.FSS_BLOCKING:
    interference = dbToLinear(computeInterferenceFssBlocking(
                     grant, channel_constraint, fss_info, eirp))

  # Compute interference to ESC protection constraint
  elif channel_constraint.entity_type is ProtectedEntityType.ESC:
    interference = dbToLinear(computeInterferenceEsc(
                     grant, channel_constraint, esc_antenna_info, eirp))

  # Compute interference to GWPZ or PPA protection constraint
  else:
    interference = dbToLinear(computeInterferencePpaGwpzPoint(
                     grant, channel_constraint, GWPZ_PPA_HEIGHT, 
                           eirp, region_type))
  
  return interference

