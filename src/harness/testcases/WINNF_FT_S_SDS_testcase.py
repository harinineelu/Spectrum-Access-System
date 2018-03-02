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

import security_testcase
from util import winnforum_testcase

DOMAIN_PROXY_CERT = os.path.join('certs', 'domain_proxy.cert')
DOMAIN_PROXY_KEY = os.path.join('certs', 'domain_proxy.key')


class SasDomainProxySecurityTestcase(security_testcase.SecurityTestCase):
  # Tests changing the SAS UUT state must explicitly call the SasReset().

  @winnforum_testcase
  def test_WINNF_FT_S_SDS_1(self):
    """New registration with TLS_RSA_WITH_AES_128_GCM_SHA256 cipher.

    Checks that SAS UUT response satisfy cipher security conditions.
    Checks that a DP registration with this configuration succeed.
    """
    self.doCbsdTestCipher('AES128-GCM-SHA256', client_cert=DOMAIN_PROXY_CERT,
                          client_key=DOMAIN_PROXY_KEY)

  @winnforum_testcase
  def test_WINNF_FT_S_SDS_2(self):
    """New registration with TLS_RSA_WITH_AES_256_GCM_SHA384 cipher.

    Checks that SAS UUT response satisfy specific security conditions.
    Checks that a DP registration with this configuration succeed.
    """
    self.doCbsdTestCipher('AES256-GCM-SHA384', client_cert=DOMAIN_PROXY_CERT,
                          client_key=DOMAIN_PROXY_KEY)

  @winnforum_testcase
  def test_WINNF_FT_S_SDS_3(self):
    """New registration with TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256 cipher.

    Checks that SAS UUT response satisfy specific security conditions.
    Checks that a DP registration with this configuration succeed.
    """
    self.doCbsdTestCipher('ECDHE-ECDSA-AES128-GCM-SHA256',
                          client_cert=DOMAIN_PROXY_CERT,
                          client_key=DOMAIN_PROXY_KEY)

  @winnforum_testcase
  def test_WINNF_FT_S_SDS_4(self):
    """New registration with TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384 cipher.

    Checks that SAS UUT response satisfy specific security conditions.
    Checks that a DP registration with this configuration succeed.
    """
    self.doCbsdTestCipher('ECDHE-ECDSA-AES256-GCM-SHA384',
                          client_cert=DOMAIN_PROXY_CERT,
                          client_key=DOMAIN_PROXY_KEY)

  @winnforum_testcase
  def test_WINNF_FT_S_SDS_5(self):
    """New registration with TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256 cipher.

    Checks that SAS UUT response satisfy specific security conditions.
    Checks that a DP registration with this configuration succeed.
    """
    self.doCbsdTestCipher('ECDHE-RSA-AES128-GCM-SHA256',
                          client_cert=DOMAIN_PROXY_CERT,
                          client_key=DOMAIN_PROXY_KEY)
