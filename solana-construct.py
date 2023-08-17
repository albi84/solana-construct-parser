from construct import this, If, Construct, Container, Struct, Bytes, Array, Switch, Enum, Byte, Padding, PaddedString, Int8ul, Int32ul, Int32sl, Int64ul, Int64sl, stream_size, stream_seek
from enum import IntEnum

class Version(Construct):
    def _parse(self, stream, context, path):
        B = int.from_bytes(stream.read(1))
        if 0x80 & B:
            return Container(versioned = True, version = 0x7F & B)
        else:
            stream_seek(stream, 0, 0, path)
            return Container(versioned = False)

class CompactU16(Construct):
    def _parse(self, stream, context, path):
        value = 0
        shift = 0
        while(stream_size(stream=stream) > 0 and shift < 14):
            B = int.from_bytes(stream.read(1))
            value += (B & 0x7f) << shift
            shift += 7
            if B < 0x80:
                return value

_PUBLIC_KEY = Bytes(32)

_BLOCKHASH = Bytes(32)

_HEADER = Struct(
    "required"      / Int8ul,
    "readonly"      / Int8ul,
    "notrequired"   / Int8ul
)

_ACCOUNTS = Struct(
    "count" / CompactU16(),
    "items" / Array(this.count, _PUBLIC_KEY)
)

_ACCOUNT_IDXS = Struct(
    "count" / CompactU16(),
    "items" / Array(this.count, Int8ul)
)

_INSTRUCTION = Struct(
    "program_index" / Int8ul,
    "accounts" / _ACCOUNT_IDXS,
    "datalen" / CompactU16(),
    "instruction_id_data" / Bytes(this.datalen),
    # "instruction_id_and_data" / Int32ul,
    # "instruction_data" / Bytes(this.datalen - 4)
)

_INSTRUCTIONS = Struct(
    "count" / CompactU16(),
    "items" / Array(this.count, _INSTRUCTION)
)

_LUT = Struct(
    "account" / _PUBLIC_KEY,
    "readwrite" / _ACCOUNT_IDXS,
    "readonly" / _ACCOUNT_IDXS
)
    
_LUTS = Struct(
    "count" / CompactU16(),
    "items" / Array(this.count, _LUT)
)
    
_MESSAGE = Struct(
    "transaction" / Version(),
    "header" / _HEADER,
    "accounts" / _ACCOUNTS,
    "blockhash" / _BLOCKHASH,
    "instructions" / _INSTRUCTIONS,
    "luts" / If(this.transaction.versioned, _LUTS)
)

_STRING = Struct(
    "length" / Int32ul,
    Padding(4),
    "chars" / PaddedString(this.length, "utf-8")
)

class SystemProgramInstruction(IntEnum):
    CreateAccount           = 0
    Assign                  = 1
    Transfer                = 2
    CreateAccountWithSeed   = 3
    Allocate                = 8
    AllocateWithSeed        = 9
    AssignWithSeed          = 10

_SYSTEM_PROGRAM = Struct(
    "instruction_id" / Int32ul,
    "parameters" / Switch(
        lambda this: this.instruction_id, {
            SystemProgramInstruction.CreateAccount: Struct(
                "lamports" / Int64ul,
                "space" / Int64ul,
                "owner" / _PUBLIC_KEY
            ),
            SystemProgramInstruction.Assign: Struct(
                "name" / _PUBLIC_KEY
            ),
            SystemProgramInstruction.Transfer: Struct(
                "lamports" / Int64ul
            ),
            SystemProgramInstruction.CreateAccountWithSeed: Struct(
                "name" / _PUBLIC_KEY,
                "seed" / _STRING,
                "lamports" / Int64ul,
                "space" / Int64ul,
                "owner" / _PUBLIC_KEY
            ),
            SystemProgramInstruction.Allocate: Struct(
                "space" / Int64ul
            ),
            SystemProgramInstruction.AllocateWithSeed: Struct(
                "base" / _PUBLIC_KEY,
                "seed" / _STRING,
                "space" / Int64ul,
                "owner" / _PUBLIC_KEY
            ),
            SystemProgramInstruction.AssignWithSeed: Struct(
                "base" / _PUBLIC_KEY,
                "seed" / _STRING,
                "owner" / _PUBLIC_KEY
            )
        }
    )
)

class StakeProgramInstruction(IntEnum):
    Initialize                  = 0
    Authorize                   = 1
    DelegateStake               = 2
    Split                       = 3
    Withdraw                    = 4
    Deactivate                  = 5
    SetLockup                   = 6
    Merge                       = 7
    AuthorizeWithSeed           = 8
    InitializeChecked           = 9
    AuthorizeChecked            = 10
    AuthorizeCheckedWithSeed    = 11
    SetLockupChecked            = 12

_STAKE_AUTHORIZE = Enum(Byte, Staker=0, Withdrawer=1)

_AUTHORIZED = Struct(
    "staker" / _PUBLIC_KEY,
    "withdrawer" / _PUBLIC_KEY
)

_LOCKUP = Struct(
    "unix_timestamp" / Int64ul,
    "epoch" / Int64ul,
    "custodian" / _PUBLIC_KEY
)

_LOCKUP_ARGS = Struct(
    "unix_timestamp" / Int64ul,
    "epoch" / Int64ul,
    "custodian" / _PUBLIC_KEY
)

_AUTHORIZE_WITH_SEED_ARGS = Struct(
    "new_authorized_pubkey" / _PUBLIC_KEY,
    "stake_authorize" / _STAKE_AUTHORIZE,
    "authority_seed" / _STRING,
    "authority_owner" / _PUBLIC_KEY
)

_AUTHORIZE_CHECKED_WITH_SEED_ARGS = Struct(
    "stake_authorize" / _STAKE_AUTHORIZE,
    "authority_seed" / _STRING,
    "authority_owner" / _PUBLIC_KEY
)

_LOCKUP_CHECKED_ARGS = Struct(
    "unix_timestamp" / Int64ul,
    "epoch" / Int64ul
)

_STAKE_PROGRAM = Struct(
    "instruction_id" / Int32ul,
    "parameters" / Switch(
        lambda this: this.instruction_id, {
            StakeProgramInstruction.Initialize: Struct(
                "authorized" / _AUTHORIZED,
                "lockup" / _LOCKUP
            ),
            StakeProgramInstruction.Authorize: Struct(
                "pubkey" / _PUBLIC_KEY,
                "stake_authorize" / _STAKE_AUTHORIZE,
            ),
            StakeProgramInstruction.DelegateStake: Struct(
            ),
            StakeProgramInstruction.Split: Struct(
                "lamports" / Int64ul,
            ),
            StakeProgramInstruction.Withdraw: Struct(
                "lamports" / Int64ul
            ),
            StakeProgramInstruction.Deactivate: Struct(
            ),
            StakeProgramInstruction.SetLockup: Struct(
                "lockupargs" / _LOCKUP_ARGS
            ),
            StakeProgramInstruction.Merge: Struct(
            ),
            StakeProgramInstruction.AuthorizeWithSeed: Struct(
                "authorize_with_seed_args" / _AUTHORIZE_WITH_SEED_ARGS
            ),
            StakeProgramInstruction.InitializeChecked: Struct(
            ),
            StakeProgramInstruction.AuthorizeChecked: Struct(
                "stake_authorize" / _STAKE_AUTHORIZE
            ),
            StakeProgramInstruction.AuthorizeCheckedWithSeed: Struct(
                "authorize_checked_with_seed_args" / _AUTHORIZE_CHECKED_WITH_SEED_ARGS
            ),
            StakeProgramInstruction.SetLockupChecked: Struct(
                "lockup_checked_args" / _LOCKUP_CHECKED_ARGS
            )
        }
    )
)



# open data source file
for path in ["input_legacy_1.hex", "input_legacy_2.hex", "input_versioned.hex"]:
    with open(path,"r") as file:
        data = bytearray.fromhex(file.read())

        # parse raw message from file
        result = _MESSAGE.parse(data)
        
        for instruction in result["instructions"]["items"]:
            program_id = result["accounts"]["items"][instruction["program_index"]].hex()
            if program_id == "0000000000000000000000000000000000000000000000000000000000000000":
                parameters = _SYSTEM_PROGRAM.parse(instruction["instruction_id_data"])
            elif program_id == "06a1d8179137542a983437bdfe2a7ab2557f535c8a78722b68a49dc000000000":
                parameters = _STAKE_PROGRAM.parse(instruction["instruction_id_data"])
            else:
                print("Unknown program id: " + program_id)

