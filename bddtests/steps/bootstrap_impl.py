# Copyright IBM Corp. 2016 All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from behave import *
import bdd_grpc_util
import endorser_util
import bdd_test_util
import bootstrap_util
import orderer_util
import compose
import time

class ChannelCreationInfo:
    'Used to store the information needed to construct Config TX for orderer broadcast to create a new channel'
    def __init__(self, channelId, channelCreationPolicyName, signedConfigEnvelope):
        self.channelId = channelId
        self.channelCreationPolicyName = channelCreationPolicyName
        self.config_update_envelope = signedConfigEnvelope

    def __repr__(self):
        return "channelId = {0}\nchannelCreationPolicyName={1}\nconfigUpdateEnvelope={2}\n".format(self.channelId,
                                                                                                   self.channelCreationPolicyName,
                                                                                                   str(
                                                                                                       self.config_update_envelope))



@given(u'the orderer network has organizations')
def step_impl(context):
    assert 'table' in context, "Expected table of orderer organizations"
    directory = bootstrap_util.getDirectory(context)
    for row in context.table.rows:
        org = directory.getOrganization(row['Organization'], shouldCreate = True)
        org.addToNetwork(bootstrap_util.Network.Orderer)


@given(u'user requests role of orderer admin by creating a key and csr for orderer and acquires signed certificate from organization')
def step_impl(context):
    assert 'table' in context, "Expected table with triplet of User/Orderer/Organization"
    directory = bootstrap_util.getDirectory(context)
    for row in context.table.rows:
        directory.registerOrdererAdminTuple(row['User'], row['Orderer'], row['Organization'])

@given(u'user requests role for peer by creating a key and csr for peer and acquires signed certificate from organization')
def step_impl(context):
    assert 'table' in context, "Expected table with triplet of User/Peer/Organization"
    directory = bootstrap_util.getDirectory(context)
    for row in context.table.rows:
        directory.registerOrdererAdminTuple(row['User'], row['Peer'], row['Organization'])

@given(u'the peer network has organizations')
def step_impl(context):
    assert 'table' in context, "Expected table of peer network organizations"
    directory = bootstrap_util.getDirectory(context)
    for row in context.table.rows:
        org = directory.getOrganization(row['Organization'], shouldCreate = True)
        org.addToNetwork(bootstrap_util.Network.Peer)

@given(u'a ordererBootstrapAdmin is identified and given access to all public certificates and orderer node info')
def step_impl(context):
    directory = bootstrap_util.getDirectory(context)
    assert len(directory.ordererAdminTuples) > 0, "No orderer admin tuples defined!!!"
    # Simply create the user
    bootstrap_util.getOrdererBootstrapAdmin(context, shouldCreate=True)

@given(u'the ordererBootstrapAdmin creates the genesis block "{ordererGenesisBlockName}" for chain "{ordererSystemChainIdName}" for network config policy "{networkConfigPolicy}" and consensus "{consensusType}" using chain creators policies')
def step_impl(context, ordererGenesisBlockName, ordererSystemChainIdName, networkConfigPolicy, consensusType):
    ordererBootstrapAdmin = bootstrap_util.getOrdererBootstrapAdmin(context)
    ordererSystemChainIdGUUID = ordererBootstrapAdmin.tags[ordererSystemChainIdName]
    # Now collect the named signed config items
    configGroups =[]
    for row in context.table.rows:
        configGroupName = row['ConfigGroup Names']
        configGroups += ordererBootstrapAdmin.tags[configGroupName]
    # Concatenate signedConfigItems

    # Construct block
    (genesisBlock,envelope) = bootstrap_util.createGenesisBlock(context, ordererSystemChainIdGUUID, consensusType, signedConfigItems=configGroups)
    ordererBootstrapAdmin.setTagValue(ordererGenesisBlockName, genesisBlock)
    bootstrap_util.OrdererGensisBlockCompositionCallback(context, genesisBlock)
    bootstrap_util.PeerCompositionCallback(context)

@given(u'the orderer admins inspect and approve the genesis block for chain "{chainId}"')
def step_impl(context, chainId):
    pass

@given(u'the orderer admins use the genesis block for chain "{chainId}" to configure orderers')
def step_impl(context, chainId):
    pass
    #raise NotImplementedError(u'STEP: Given the orderer admins use the genesis block for chain "testchainid" to configure orderers')

@given(u'the ordererBootstrapAdmin generates a GUUID to identify the orderer system chain and refer to it by name as "{ordererSystemChainId}"')
def step_impl(context, ordererSystemChainId):
    directory = bootstrap_util.getDirectory(context)
    ordererBootstrapAdmin = bootstrap_util.getOrdererBootstrapAdmin(context)
    ordererBootstrapAdmin.setTagValue(ordererSystemChainId, bootstrap_util.GetUUID())


@given(u'the ordererBootstrapAdmin creates a chain creators policy "{chainCreatePolicyName}" (network name) for peer orgs who wish to form a network using orderer system chain "{ordererSystemChainId}"')
def step_impl(context, chainCreatePolicyName, ordererSystemChainId):
    directory = bootstrap_util.getDirectory(context)


    ordererBootstrapAdmin = bootstrap_util.getOrdererBootstrapAdmin(context)
    ordererSystemChainIdGuuid = ordererBootstrapAdmin.tags[ordererSystemChainId]

    # Collect the orgs from the table
    orgNames = [row['Organization'] for row in context.table.rows]
    bootstrap_util.addOrdererBootstrapAdminOrgReferences(context, chainCreatePolicyName, orgNames)

    chainCreatorsOrgsPolicySignedConfigItem = \
        bootstrap_util.createChainCreatorsPolicy(context=context, chainCreatePolicyName=chainCreatePolicyName, chaindId=ordererSystemChainIdGuuid, orgNames=orgNames)

    ordererBootstrapAdmin.setTagValue(chainCreatePolicyName, [chainCreatorsOrgsPolicySignedConfigItem])


@given(u'the ordererBootstrapAdmin runs the channel template tool to create the orderer configuration template "{templateName}" for application developers using orderer "{ordererComposeService}"')
def step_impl(context, templateName, ordererComposeService):
    pass


@given(u'the ordererBootstrapAdmin distributes orderer configuration template "template1" and chain creation policy name "chainCreatePolicy1"')
def step_impl(context):
    pass


@given(u'the user "{userName}" creates a peer template "{templateName}" with chaincode deployment policy using chain creation policy name "{chainCreatePolicyName}" and peer organizations')
def step_impl(context, userName, templateName, chainCreatePolicyName):
    ' At the moment, only really defining MSP Config Items (NOT SIGNED)'
    directory = bootstrap_util.getDirectory(context)
    user = directory.getUser(userName)
    user.setTagValue(templateName, [directory.getOrganization(row['Organization']) for row in context.table.rows])


@given(u'the user "{userName}" creates a ConfigUpdateEnvelope "{createChannelSignedConfigEnvelope}"')
def step_impl(context, userName, createChannelSignedConfigEnvelope):
    directory = bootstrap_util.getDirectory(context)
    user = directory.getUser(userName)
    ordererBootstrapAdmin = bootstrap_util.getOrdererBootstrapAdmin(context)


    channelID = context.table.rows[0]["ChannelID"]
    chainCreationPolicyName = context.table.rows[0]["Chain Creation Policy Name"]
    templateName = context.table.rows[0]["Template"]
    # Loop through templates referenced orgs
    mspOrgNames = [org.name for org in user.tags[templateName]]
    signedMspConfigItems = bootstrap_util.getSignedMSPConfigItems(context=context, orgNames=mspOrgNames)

    # Add the anchors signed config Items
    anchorSignedConfigItemsName = context.table.rows[0]["Anchors"]
    signedAnchorsConfigItems = user.tags[anchorSignedConfigItemsName]

    # Intermediate step until template tool is ready
    channel_config_groups = bootstrap_util.createSignedConfigItems(directory, configGroups=signedMspConfigItems + signedAnchorsConfigItems)

    # bootstrap_util.setMetaPolicy(channelId=channelID, channgel_config_groups=channgel_config_groups)

    #NOTE: Conidered passing signing key for appDeveloper, but decided that the peer org signatures they need to collect subsequently should be proper way
    config_update_envelope = bootstrap_util.createConfigUpdateEnvelope(channelConfigGroup=channel_config_groups, chainId=channelID, chainCreationPolicyName=chainCreationPolicyName)

    user.setTagValue(createChannelSignedConfigEnvelope, ChannelCreationInfo(channelID, chainCreationPolicyName, config_update_envelope))

    # Construct TX Config Envelope, broadcast, expect success, and then connect to deliver to revtrieve block.
    # Make sure the blockdata exactly the TxConfigEnvelope I submitted.
    # txConfigEnvelope = bootstrap_util.createConfigTxEnvelope(chainId=channelID, signedConfigEnvelope=signedConfigEnvelope)


@given(u'the following application developers are defined for peer organizations and each saves their cert as alias')
def step_impl(context):
    assert 'table' in context, "Expected table with triplet of Developer/ChainCreationPolicyName/Organization"
    directory = bootstrap_util.getDirectory(context)
    for row in context.table.rows:
        userName = row['Developer']
        nodeAdminNamedTuple = directory.registerOrdererAdminTuple(userName, row['ChainCreationPolicyName'], row['Organization'])
        user = directory.getUser(userName)
        user.setTagValue(row['AliasSavedUnder'], nodeAdminNamedTuple)

@given(u'the user "{userName}" collects signatures for ConfigUpdateEnvelope "{createChannelSignedConfigEnvelopeName}" from peer orgs')
def step_impl(context, userName, createChannelSignedConfigEnvelopeName):
    assert 'table' in context, "Expected table of peer organizations"
    directory = bootstrap_util.getDirectory(context)
    user = directory.getUser(userName=userName)
    # Get the ChannelCreationInfo object that holds the signedConfigEnvelope
    channelCreationInfo = user.tags[createChannelSignedConfigEnvelopeName]
    config_update_envelope = channelCreationInfo.config_update_envelope
    for row in context.table.rows:
        org = directory.getOrganization(row['Organization'])
        assert bootstrap_util.Network.Peer in org.networks, "Organization '{0}' not in Peer network".format(org.name)
        bootstrap_util.BootstrapHelper.addSignatureToSignedConfigItem(config_update_envelope, (org, org.getSelfSignedCert()))
    # print("Signatures for signedConfigEnvelope:\n {0}\n".format(signedConfigEnvelope.Items[0]))

@given(u'the user "{userName}" creates a ConfigUpdate Tx "{configUpdateTxName}" using signed ConfigUpdateEnvelope "{createChannelSignedConfigEnvelopeName}"')
def step_impl(context, userName, configUpdateTxName, createChannelSignedConfigEnvelopeName):
    directory = bootstrap_util.getDirectory(context)
    user = directory.getUser(userName=userName)
    channelCreationInfo = user.tags[createChannelSignedConfigEnvelopeName]
    #TODO: this is temporary until partial update is supported.  Normally you would just return
    # this message and send directly to broadcast.
    envelope_for_config_update = bootstrap_util.createConfigUpdateTxEnvelope(channelCreationInfo.channelId, channelCreationInfo.config_update_envelope)
    user.setTagValue(configUpdateTxName, envelope_for_config_update)

@given(u'the user "{userName}" broadcasts ConfigUpdate Tx "{configTxName}" to orderer "{orderer}" to create channel "{channelId}"')
def step_impl(context, userName, configTxName, orderer, channelId):
    directory = bootstrap_util.getDirectory(context)
    user = directory.getUser(userName=userName)
    configTxEnvelope = user.tags[configTxName]
    bootstrap_util.broadcastCreateChannelConfigTx(context=context, composeService=orderer, chainId=channelId, user=user, configTxEnvelope=configTxEnvelope)

@when(u'the user "{userName}" broadcasts transaction "{transactionAlias}" to orderer "{orderer}" on channel "{channelId}"')
def step_impl(context, userName, transactionAlias, orderer, channelId):
    directory = bootstrap_util.getDirectory(context)
    user = directory.getUser(userName=userName)
    transaction = user.tags[transactionAlias]
    bootstrap_util.broadcastCreateChannelConfigTx(context=context, composeService=orderer, chainId=channelId, user=user, configTxEnvelope=transaction)


@when(u'user "{userName}" connects to deliver function on orderer "{composeService}"')
def step_impl(context, userName, composeService):
    directory = bootstrap_util.getDirectory(context)
    user = directory.getUser(userName=userName)
    user.connectToDeliverFunction(context, composeService)

@when(u'user "{userName}" sends deliver a seek request on orderer "{composeService}" with properties')
def step_impl(context, userName, composeService):
    directory = bootstrap_util.getDirectory(context)
    user = directory.getUser(userName=userName)
    row = context.table.rows[0]
    chainID = row['ChainId']
    start, end, = orderer_util.convertSeek(row['Start']), orderer_util.convertSeek(row['End'])
    print("Start and end = {0}/{1}".format(start, end))
    print("")
    streamHelper = user.getDelivererStreamHelper(context, composeService)
    streamHelper.seekToRange(chainID=chainID, start = start, end = end)

@then(u'user "{userName}" should get a delivery "{deliveryName}" from "{composeService}" of "{expectedBlocks}" blocks with "{numMsgsToBroadcast}" messages within "{batchTimeout}" seconds')
def step_impl(context, userName, deliveryName, composeService, expectedBlocks, numMsgsToBroadcast, batchTimeout):
    directory = bootstrap_util.getDirectory(context)
    user = directory.getUser(userName=userName)
    streamHelper = user.getDelivererStreamHelper(context, composeService)

    blocks = streamHelper.getBlocks()

    # Verify block count
    assert len(blocks) == int(expectedBlocks), "Expected {0} blocks, received {1}".format(expectedBlocks, len(blocks))
    user.setTagValue(deliveryName, blocks)

@when(u'user "{userName}" using cert alias "{certAlias}" requests to join channel using genesis block "{genisisBlockName}" on peers with result "{joinChannelResult}"')
def step_impl(context, userName, certAlias, genisisBlockName, joinChannelResult):
    timeout = 10
    directory = bootstrap_util.getDirectory(context)
    user = directory.getUser(userName)
    # Find the cert using the cert tuple information saved for the user under certAlias
    signersCert = directory.findCertForNodeAdminTuple(user.tags[certAlias])

    # Retrieve the genesis block from the returned value of deliver (Will be list with first block as genesis block)
    genesisBlock = user.tags[genisisBlockName][0]
    ccSpec = endorser_util.getChaincodeSpec("GOLANG", "", "cscc", ["JoinChain", genesisBlock.SerializeToString()])
    proposal = endorser_util.createInvokeProposalForBDD(context, ccSpec=ccSpec, chainID="",signersCert=signersCert, Mspid=user.tags[certAlias].organization, type="CONFIG")
    signedProposal = endorser_util.signProposal(proposal=proposal, entity=user, signersCert=signersCert)

    # Send proposal to each specified endorser, waiting 'timeout' seconds for response/error
    endorsers = [row['Peer'] for row in context.table.rows]
    proposalResponseFutures = [endorserStub.ProcessProposal.future(signedProposal, int(timeout)) for endorserStub in endorser_util.getEndorserStubs(context, endorsers)]
    resultsDict =  dict(zip(endorsers, [respFuture.result() for respFuture in proposalResponseFutures]))
    user.setTagValue(joinChannelResult, resultsDict)



@given(u'the ordererBoostrapAdmin creates MSP configuration "{mspConfigItemsName}" for orderer system chain "{ordererSystemChainIdName}" for every MSP referenced by the policies')
def step_impl(context, ordererSystemChainIdName, mspConfigItemsName):
    assert 'table' in context, "Expected table of policy names"
    directory = bootstrap_util.getDirectory(context)
    ordererBootstrapAdmin = bootstrap_util.getOrdererBootstrapAdmin(context)
    ordererSystemChainIdGUUID = ordererBootstrapAdmin.tags[ordererSystemChainIdName]
    mspSignedConfigItems = bootstrap_util.getMspConfigItemsForPolicyNames(context, policyNames=[row['PolicyName'] for row in context.table.rows])
    ordererBootstrapAdmin.setTagValue(mspConfigItemsName, mspSignedConfigItems)

@given(u'the ordererBoostrapAdmin creates the chain creation policy names "{chainCreationPolicyNames}" for orderer system chain "{ordererSystemChainIdName}" with policies')
def step_impl(context, chainCreationPolicyNames, ordererSystemChainIdName):
    ordererBootstrapAdmin = bootstrap_util.getOrdererBootstrapAdmin(context)
    ordererSystemChainIdGUUID = ordererBootstrapAdmin.tags[ordererSystemChainIdName]
    policyNames = [row['PolicyName'] for row in context.table.rows]
    chainCreationPolicyNamesConfigItem = bootstrap_util.createChainCreationPolicyNames(context, chainCreationPolicyNames=policyNames, chaindId=ordererSystemChainIdGUUID)
    ordererBootstrapAdmin.setTagValue(chainCreationPolicyNames, [chainCreationPolicyNamesConfigItem])

@then(u'user "{userName}" expects result code for "{proposalResponseName}" of "{proposalResponseResultCode}" from peers')
def step_impl(context, userName, proposalResponseName, proposalResponseResultCode):
    directory = bootstrap_util.getDirectory(context)
    user = directory.getUser(userName=userName)
    peerToProposalResponseDict = user.tags[proposalResponseName]
    unexpectedResponses = [(composeService,proposalResponse) for composeService, proposalResponse in peerToProposalResponseDict.items() if proposalResponse.response.payload != proposalResponseResultCode]
    print("ProposalResponse: \n{0}\n".format(proposalResponse))
    print("")

@given(u'the user "{userName}" creates an peer anchor set "{anchorSetName}" for channel "{channelName}" for orgs')
def step_impl(context, userName, anchorSetName, channelName):
    directory = bootstrap_util.getDirectory(context)
    user = directory.getUser(userName=userName)
    nodeAdminTuples = [directory.findNodeAdminTuple(row['User'], row['Peer'], row['Organization']) for row in context.table.rows]
    user.setTagValue(anchorSetName, bootstrap_util.getAnchorPeersConfigGroup(context=context, nodeAdminTuples=nodeAdminTuples))

@given(u'we compose "{composeYamlFile}"')
def step_impl(context, composeYamlFile):
    # time.sleep(10)              # Should be replaced with a definitive interlock guaranteeing that all peers/membersrvc are ready
    composition = compose.Composition(context, composeYamlFile)
    context.compose_containers = composition.containerDataList
    context.composition = composition

@given(u'I wait "{seconds}" seconds')
def step_impl(context, seconds):
    time.sleep(float(seconds))

@when(u'I wait "{seconds}" seconds')
def step_impl(context, seconds):
    time.sleep(float(seconds))

@then(u'I wait "{seconds}" seconds')
def step_impl(context, seconds):
    time.sleep(float(seconds))

@given(u'user "{userNameSource}" gives "{objectAlias}" to user "{userNameTarget}"')
def step_impl(context, userNameSource, objectAlias, userNameTarget):
    directory = bootstrap_util.getDirectory(context)
    userSource = directory.getUser(userName=userNameSource)
    userTarget = directory.getUser(userName=userNameTarget)
    userTarget.setTagValue(objectAlias, userSource.tags[objectAlias])
