*** Settings ***
Library    RequestsLibrary
Library    OperatingSystem
Library    Collections

*** Keywords ***
Create RelayHub Sessions
    ${gateway}=    Get Environment Variable    BASE_URL    http://127.0.0.1:8080
    ${partner}=    Get Environment Variable    PARTNER_BASE_URL    http://127.0.0.1:8083
    ${token}=      Get Environment Variable    PARTNER_ADMIN_TOKEN    local-test-token
    Set Suite Variable    ${PARTNER_TOKEN}    ${token}
    Create Session    gateway    ${gateway}
    Create Session    partner    ${partner}

Reset Partner State
    &{headers}=    Create Dictionary    X-Admin-Token=${PARTNER_TOKEN}
    DELETE On Session    partner    /__admin/state    headers=${headers}    expected_status=204

New Message Id
    ${date}=      Evaluate    datetime.datetime.now(datetime.UTC).strftime("%Y%m%d")    modules=datetime
    ${suffix}=    Evaluate    uuid.uuid4().hex[:8].upper()    modules=uuid
    RETURN        MSG-${date}-${suffix}

Build JSON Transmission
    [Arguments]    ${message_id}
    &{location}=    Create Dictionary    x=${41.2}    y=${23.9}
    &{payload}=     Create Dictionary    event=robot-smoke    unit=alpha-7    location=${location}    internal_note=filter-me
    &{body}=        Create Dictionary
    ...             message_id=${message_id}
    ...             schema_version=1.0
    ...             source_system=ROBOT_CLIENT
    ...             target_system=PARTNER_B
    ...             priority=HIGH
    ...             data_sensitivity=CONTROLLED
    ...             payload_format=JSON
    ...             payload=${payload}
    RETURN          ${body}

Transmission Should Be Delivered
    [Arguments]    ${message_id}
    ${response}=    GET On Session    gateway    /api/v1/transmissions/${message_id}    expected_status=200
    Should Be Equal As Strings    ${response.json()}[status]    DELIVERED
