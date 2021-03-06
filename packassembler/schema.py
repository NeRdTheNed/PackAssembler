from functools import total_ordering
from mongoengine import *

# Mod targets
TARGETS = ('server', 'client', 'both')
# Minecraft versions
MCVERSIONS = ('1.7.10', '1.7.2', '1.6.4')
# Forge version length
FV = 16


class User(Document):
    # Username, limited for formatting purposes
    username = StringField(required=True, min_length=6, max_length=32, unique=True)
    # Password, should be bcrypt hashed
    password = BinaryField(required=True)
    # Email, should be validated on client side first
    email = EmailField(required=True, unique=True)
    # Group, used for authorization
    group = StringField(required=True, default='user')
    # Avatar
    avatar_type = IntField(default=0)
    email_hash = StringField(default='')
    # Last login
    last_login = DateTimeField()

    # Codes
    ## Activation code
    activate = IntField()
    ## Password reset code
    reset = IntField()

    meta = {
        'indexes': ['username'],
        'ordering': ['username']
    }


class ModVersion(Document):
    # Minecraft version
    mc_version = StringField(required=True, choices=MCVERSIONS)
    # Minecraft Forge version
    ## If not defined, default to any version
    forge_min = StringField(max_length=FV)
    # Dependencies
    depends = ListField(ReferenceField('Mod'))
    # Actual version number
    version = StringField(required=True)
    # A link to a changelog
    changelog = URLField()
    # The file itself
    mod_file = FileField(collection_name='modfs')
    mod_file_url = URLField()
    mod_file_url_md5 = StringField(max_length=32)
    # Reference Mod ModVersion belongs to
    mod = ReferenceField('Mod') # Required
    # Is a development version
    devel = BooleanField(default=False)

    @property
    def md5(self):
        return self.mod_file.md5 if self.mod_file else self.mod_file_url_md5


class Banner(EmbeddedDocument):
    # Actual Image
    image = URLField(required=True)
    # Color of text on banner (title, etc)
    text_color = StringField(min_length=4, max_length=7, default='#FFFFFF')


@total_ordering
class Mod(Document):
    def __lt__(self, other):
        return self.name.lower() < other.name.lower()

    def __eq__(self, other):
        try:
            return self.name == other.name
        except AttributeError:
            return False

    # Information
    ## Name of mod
    name = StringField(required=True, max_length=32, unique=True)
    ## Readable id
    rid = StringField(required=True, unique=True)
    ## Description of mod
    description = StringField()
    ## Author(s) of the mod
    author = StringField(required=True, max_length=32)
    ## Where to run mod (server, client, or both?)
    target = StringField(choices=TARGETS, default='both')
    ## Mod homepage
    url = URLField(required=True)
    ## Permission from author (unless uploader is the author)
    permission = StringField()
    ## Donation URL
    donate = URLField()
    # Versions of the mod (and compatibility information)
    versions = ListField(ReferenceField(ModVersion, reverse_delete_rule=PULL))
    # Owner: Full permissions
    owner = ReferenceField(User, reverse_delete_rule=NULLIFY)
    # Is outdated?
    outdated = BooleanField(required=True, default=False)
    # Formatting extras
    banner = EmbeddedDocumentField(Banner)

    meta = {
        'ordering': ['name']
    }

Mod.register_delete_rule(ModVersion, 'mod', CASCADE)
Mod.register_delete_rule(ModVersion, 'depends', PULL)


class PackBuild(Document):
    # Build number
    revision = IntField(required=True)
    # Mod versoins
    mod_versions = ListField(ReferenceField(ModVersion, reverse_delete_rule=DENY))
    # Configuration, should be on external server
    config = URLField()
    # Version information
    mc_version = StringField(required=True, choices=MCVERSIONS)
    forge_version = StringField(required=True, max_length=FV)
    # Reference Pack PackBuild belongs to
    pack = ReferenceField('Pack', required=True)


class Pack(Document):
    # Information
    name = StringField(required=True, unique=True)
    # Readable id
    rid = StringField(required=True, unique=True)
    # Mod and Base Pack Lists
    mods = ListField(ReferenceField(Mod, reverse_delete_rule=DENY))
    bases = ListField(ReferenceField('Pack', reverse_delete_rule=PULL))
    # Builds
    builds = ListField(ReferenceField(PackBuild, reverse_delete_rule=PULL))
    # Latest PackBuild revision
    latest = IntField(required=True, default=0)
    # Owner of Pack
    owner = ReferenceField(User, required=True, reverse_delete_rule=CASCADE)
    # Formatting extras
    banner = EmbeddedDocumentField(Banner)
    # Base
    base = BooleanField(default=False)

    meta = {
        'ordering': ['name'],
    }

Pack.register_delete_rule(PackBuild, 'pack', CASCADE)


class Server(Document):
    # Information
    name = StringField(required=True, max_length=32, unique=True)
    url = URLField()
    host = StringField(required=True)
    port = IntField(required=True)
    # Readable id
    rid = StringField(required=True, unique=True)
    # Pack used
    build = ReferenceField('PackBuild', reverse_delete_rule=NULLIFY)
    # Owner
    owner = ReferenceField(User, required=True, reverse_delete_rule=CASCADE)
    # Configuration, should be on external server
    config = URLField()
    # Formatting extras
    banner = EmbeddedDocumentField(Banner)

    meta = {
        'ordering': ['name']
    }


class Setting(DynamicDocument):
    # Key
    key = StringField(required=True, max_length=16, unique=True)
