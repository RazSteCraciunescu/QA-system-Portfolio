*** Settings ***
Documentation    Small acceptance pack intended for release smoke verification.
Resource         resources/api.resource
Suite Setup      Create RelayHub Sessions
Test Setup       Reset Partner State

*** Test Cases ***
Gateway Is Ready
    [Tags]    smoke    health
    ${response}=    GET On Session    gateway    /health/ready    expected_status=200
    Should Be Equal As Strings    ${response.json()}[status]    READY

Valid Message Reaches Partner
    [Tags]    smoke    api    interoperability
    ${message_id}=    New Message Id
    ${body}=          Build JSON Transmission    ${message_id}
    ${response}=      POST On Session    gateway    /api/v1/transmissions    json=${body}    expected_status=202
    Should Be Equal As Strings    ${response.json()}[message_id]    ${message_id}
    Wait Until Keyword Succeeds    15 sec    300 ms    Transmission Should Be Delivered    ${message_id}

Duplicate Message Is Rejected
    [Tags]    regression    negative
    ${message_id}=    New Message Id
    ${body}=          Build JSON Transmission    ${message_id}
    POST On Session    gateway    /api/v1/transmissions    json=${body}    expected_status=202
    ${duplicate}=     POST On Session    gateway    /api/v1/transmissions    json=${body}    expected_status=409
    Should Be Equal As Strings    ${duplicate.json()}[error][code]    DUPLICATE_MESSAGE_ID
