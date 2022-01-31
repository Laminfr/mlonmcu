import yaml

from .options import parse_model_options_for_backend


def parse_metadata(path):
    content = {}
    with open(path, "r") as yamlfile:
        try:
            content = yaml.safe_load(yamlfile)
        except yaml.YAMLError as err:
            raise RuntimeError(f"Could not open YAML file: {path}") from err
    return content


# class ModelOperator:
#     def __init__(self, name, custom=False, registration=None):
#         self.name = name
#         self.custom = custom
#         self.registration = registration
#
#
# class ModelMetadata:
#     def __init__(
#         self,
#         author="unknown",
#         description="",
#         created_at=None,
#         references=None,
#         comment=None,
#         backend_options_map=None,
#     ):
#         self.author = author if author is not None else "unknown"
#         self.description = description if description is not None else ""
#         self.created_at = created_at
#         self.refrences = references if references is not None else []
#         self.comment = comment
#         self.backend_options_map = (
#             backend_options_map if backend_options_map is not None else {}
#         )
#
#     def __repr__(self):
#         return "ModelMetadata(" + str(vars(self)) + ")"
#
#
# class TfLitelMetadata(ModelMetadata):
#     def __init__(
#         self,
#         author="unknown",
#         description="",
#         created_at=None,
#         references=None,
#         comment=None,
#         backend_options_map=None,
#         operators=[],
#     ):
#         super().__init__(
#             author=author,
#             description=description,
#             created_at=created_at,
#             references=references,
#             comment=comment,
#             backend_options_map=backend_options_map,
#             operators=operators,
#         )
#         self.operators = operators
#
#
# def parse_metadata(path):
#     with open(path, "r") as yamlfile:
#         try:
#             content = yaml.safe_load(yamlfile)
#             if not content:
#                 # file empty
#                 return ModelMetadata()
#             if "author" in content:
#                 author = content["author"]
#             else:
#                 author = None
#             if "description" in content:
#                 description = content["description"]
#             else:
#                 description = None
#             if "created_at" in content:
#                 created_at = content["created_at"]
#             else:
#                 created_at = None
#             if "references" in content:
#                 references = content["references"]
#                 assert isinstance(references, list)
#             else:
#                 references = []
#             if "comment" in content:
#                 comment = content["comment"]
#             else:
#                 comment = None
#             backend_options_map = {}
#             if "backends" in content:
#                 backends = content["backends"]
#                 for backend in backends:
#                     backend_options = parse_model_options_for_backend(
#                         backend, backends[backend]
#                     )
#                     backend_options_map[backend] = backend_options
#             metadata = ModelMetadata(
#                 author=author,
#                 description=description,
#                 created_at=created_at,
#                 references=references,
#                 comment=comment,
#                 backend_options_map=backend_options_map,
#             )
#             return metadata
#         except yaml.YAMLError as err:
#             raise RuntimeError(f"Could not open YAML file: {path}") from err
#
#     return None
