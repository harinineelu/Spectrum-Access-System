#    Copyright 2018 SAS Project Authors. All Rights Reserved.
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
import os
from OpenSSL import SSL
import security_testcase
from util import winnforum_testcase, configurable_testcase, writeConfig, loadConfig

SAS_CERT = os.path.join('certs', 'sas.cert')
SAS_KEY = os.path.join('certs', 'sas.key')
SAS_URL = 'https://fake.sas.url.not.used.org/v1.2'


class SasToSasSecurityTestcase(security_testcase.SecurityTestCase):
  # Tests changing the SAS UUT state must explicitly call the SasReset().

  @winnforum_testcase
  def test_WINNF_FT_S_SSS_1(self):
    """New registration with TLS_RSA_WITH_AES_128_GCM_SHA256 cipher.

    Checks that SAS UUT response satisfy cipher security conditions.
    Checks that a SAS registration with this configuration succeed.
    """
    self.doSasTestCipher('AES128-GCM-SHA256',
                         client_cert=SAS_CERT, client_key=SAS_KEY,
                         client_url=SAS_TH_URL)

  @winnforum_testcase
  def test_WINNF_FT_S_SSS_2(self):
    """New registration with TLS_RSA_WITH_AES_256_GCM_SHA384 cipher.

    Checks that SAS UUT response satisfy specific security conditions.
    Checks that a SAS registration with this configuration succeed.
    """
    self.doSasTestCipher('AES256-GCM-SHA384',
                         client_cert=SAS_CERT, client_key=SAS_KEY,
                         client_url=SAS_TH_URL)

  @winnforum_testcase
  def test_WINNF_FT_S_SSS_3(self):
    """New registration with TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256 cipher.

    Checks that SAS UUT response satisfy specific security conditions.
    Checks that a SAS registration with this configuration succeed.
    """
    self.doSasTestCipher('ECDHE-ECDSA-AES128-GCM-SHA256',
                         client_cert=SAS_CERT, client_key=SAS_KEY,
                         client_url=SAS_TH_URL)

  @winnforum_testcase
  def test_WINNF_FT_S_SSS_4(self):
    """New registration with TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384 cipher.

    Checks that SAS UUT response satisfy specific security conditions.
    Checks that a SAS registration with this configuration succeed.
    """
    self.doSasTestCipher('ECDHE-ECDSA-AES256-GCM-SHA384',
                         client_cert=SAS_CERT, client_key=SAS_KEY,
                         client_url=SAS_TH_URL)

  @winnforum_testcase
  def test_WINNF_FT_S_SSS_5(self):
    """New registration with TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256 cipher.

    Checks that SAS UUT response satisfy specific security conditions.
    Checks that a SAS registration with this configuration succeed.
    """
    self.doSasTestCipher('ECDHE-RSA-AES128-GCM-SHA256',
                         client_cert=SAS_CERT, client_key=SAS_KEY,
                         client_url=SAS_TH_URL)

  def generate_SSS_6_default_config(self, filename):
    """Generates the WinnForum configuration for SSS_6"""
    # Create the actual config for sas cert/key path

    config = {
        'sasCert': self.getCertFilename("unrecognized_sas.cert"),
        'sasKey': self.getCertFilename("unrecognized_sas.key")
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_SSS_6_default_config)
  def test_WINNF_FT_S_SSS_6(self, config_filename):
    """Unrecognized root of trust certificate presented during registration.

    Checks that SAS UUT response with fatal alert with unknown_ca.
    """
    config = loadConfig(config_filename)
    self.assertTlsHandshakeFailure(client_cert=config['sasCert'],
                                   client_key=config['sasKey'])

  def generate_SSS_7_default_config(self, filename):
    """Generates the WinnForum configuration for SSS_7"""
    # Create the actual config for sas cert/key path

    config = {
        'sasCert': self.getCertFilename("corrupted_sas.cert"),
        'sasKey': self.getCertFilename("corrupted_sas.key")
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_SSS_7_default_config)
  def test_WINNF_FT_S_SSS_7(self, config_filename):
    """Corrupted certificate presented during registration.

    Checks that SAS UUT response with fatal alert message.
    """
    config = loadConfig(config_filename)
    self.assertTlsHandshakeFailure(client_cert=config['sasCert'],
                                   client_key=config['sasKey'])

  def generate_SSS_8_default_config(self, filename):
    """Generates the WinnForum configuration for SSS_8"""
    # Create the actual config for sas cert/key path

    config = {
        'sasCert': self.getCertFilename("self_signed_sas.cert"),
        'sasKey': self.getCertFilename("sas.key")
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_SSS_8_default_config)
  def test_WINNF_FT_S_SSS_8(self, config_filename):
    """Self-signed certificate presented during registration.

    Checks that SAS UUT response with fatal alert message.
    """
    config = loadConfig(config_filename)
    self.assertTlsHandshakeFailure(client_cert=config['sasCert'],
                                   client_key=config['sasKey'])

  def generate_SSS_9_default_config(self, filename):
    """Generates the WinnForum configuration for SSS_9"""
    # Create the actual config for domain proxy cert/key path

    config = {
        'sasCert': self.getCertFilename("non_cbrs_signed_sas.cert"),
        'sasKey': self.getCertFilename("non_cbrs_signed_sas.key")
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_SSS_9_default_config)
  def test_WINNF_FT_S_SSS_9(self, config_filename):
    """Non-CBRS trust root signed certificate presented during registration.

    Checks that SAS UUT response with fatal alert message.
    """
    config = loadConfig(config_filename)
    self.assertTlsHandshakeFailure(client_cert=config['sasCert'],
                                   client_key=config['sasKey'])

  def generate_SSS_12_default_config(self, filename):
    """Generates the WinnForum configuration for SSS.12"""
    # Create the actual config for domain proxy cert/key path

    config = {
        'sasCert': self.getCertFilename("sas_expired.cert"),
        'sasKey': self.getCertFilename("sas_expired.key")
    }
    writeConfig(filename, config)

  @configurable_testcase(generate_SSS_12_default_config)
  def test_WINNF_FT_S_SSS_12(self, config_filename):
    """Expired certificate presented during registration.

    Checks that SAS UUT response with fatal alert message.
    """
    config = loadConfig(config_filename)
    self.assertTlsHandshakeFailure(client_cert=config['sasCert'],
                                   client_key=config['sasKey'])

  @winnforum_testcase
  def test_WINNF_FT_S_SSS_13(self):
    """ Disallowed TLS method attempted during registration.

    Checks that SAS UUT response with fatal alert message.
    """
    self.assertTlsHandshakeFailure(SAS_CERT, SAS_KEY, ssl_method=SSL.TLSv1_1_METHOD)

  @winnforum_testcase
  def test_WINNF_FT_S_SSS_14(self):
    """Invalid ciphersuite presented during registration.

    Checks that SAS UUT response with fatal alert message.
    """
    self.assertTlsHandshakeFailure(SAS_CERT, SAS_KEY, ciphers='ECDHE-RSA-AES256-GCM-SHA384')