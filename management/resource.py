from typing import Dict, Optional, Iterable
from abc import ABC, abstractmethod
from pathlib import Path
import hashlib
import os

class ResourceFile:
    def __init__(self, path: Path, ):
        self.path = path
        self.hash_ = self.hashFile(self.path, )
    
    def __hash__(self, ):
        return hash(self.hash_, )

    def __eq__(self, other: object, ):
        if not isinstance(other, (ResourceFile, )):
            return NotImplemented
        
        return self.compareFiles(self.path, other.path, )
    
    def __ne__(self, other: object, ):
        return not self.__eq__(other, )

    @staticmethod
    def hashFile(path: Path, blockSize: int = 65536, ):
        hasher = hashlib.md5()
        with open(path, "rb", ) as f:
            while True:
                block = f.read(blockSize, )
                if not block:
                    break
                hasher.update(block, )
        return hasher.hexdigest()
    
    @staticmethod
    def compareFiles(path1: Path, path2: Path, blockSize: int = 65536, ):
        f1 = open(path1, "rb", )
        f2 = open(path2, "rb", )
        while True:
            block1 = f1.read(blockSize, )
            block2 = f2.read(blockSize, )
            if not block1 and not block2:
                return True
            if block1 != block2:
                return False

class ReferenceCountedResource:
    def __init__(self, path: str, ):
        self.path = path
        self.refCount = 0

    def __eq__(self, other: object, ):
        if not isinstance(other, (ReferenceCountedResource, )):
            return NotImplemented
        
        return self.path == other.path

class ResourcePathResolver(ABC, ):
    @abstractmethod
    def importPathToRelativePath(self, path: str, ) -> str:
        ...

    @abstractmethod
    def exportPathFromRelativePath(self, path: str, ) -> str:
        ...

    @abstractmethod
    def resolveNameConflict(self, name: str, ) -> str:
        ...

    @abstractmethod
    def isImportantResource(self, fullPath: str, ) -> bool:
        ...

class ResourceManager:
    def __init__(self, rootPath: str, pathResolver: ResourcePathResolver, ):
        self.__rootPath = Path(rootPath, )
        self.__pathResolver = pathResolver
        self.__resources: Dict[ResourceFile, ReferenceCountedResource] = {}

    def getRootPath(self, ) -> str:
        return self.__rootPath.as_posix()
    
    def getPathResolver(self, ) -> ResourcePathResolver:
        return self.__pathResolver

    def clearResources(self, deleteFiles: bool = False, ):
        if deleteFiles:
            for resourceFile in self.__resources.keys():
                try:
                    if not self.__pathResolver.isImportantResource(resourceFile.path.as_posix(), ):
                        os.remove(resourceFile.path, )
                except Exception as e:
                    print(f"Failed to delete file {resourceFile.path}: {e}", )
        self.__resources.clear()

    def addResource(self, filePath: str, copyIfNotUnderRoot: bool = True, / , subFolder: str = "") -> ReferenceCountedResource:
        resourceFile = ResourceFile(Path(
            self.__rootPath / self.__pathResolver.importPathToRelativePath(filePath, ),
        ), )
        if resourceFile in self.__resources:
            resource = self.__resources[resourceFile]
            resource.refCount += 1
            return resource
        else:
            if copyIfNotUnderRoot and not resourceFile.path.is_relative_to(self.__rootPath, ):
                # Copy file to root path
                destPath = self.__rootPath / subFolder / resourceFile.path.name
                if destPath.exists():
                    destPath = self.__rootPath / self.__pathResolver.resolveNameConflict(destPath.name, )
                os.makedirs(destPath.parent, exist_ok=True, )
                with open(resourceFile.path, "rb", ) as src, open(destPath, "wb", ) as dst:
                    while True:
                        block = src.read(65536, )
                        if not block:
                            break
                        dst.write(block, )
                resourceFile = ResourceFile(destPath, )

            resource = ReferenceCountedResource(self.__pathResolver.exportPathFromRelativePath(
                resourceFile.path.relative_to(self.__rootPath, ).as_posix(),
            ), )
            resource.refCount = 1
            self.__resources[resourceFile] = resource
            return resource

    def removeResource(self, filePath: str, deleteRefIfZero: bool = False, ):
        ref = ReferenceCountedResource(filePath, )
        # Find the corresponding ResourceFile & Resource
        target = next(((rf, r) for rf, r in self.__resources.items() if r == ref), None)
        if target is not None:
            resourceFile, resource = target
            resource.refCount -= 1
            if resource.refCount <= 0 and deleteRefIfZero:
                del self.__resources[resourceFile]

    def listNotManagedFilesUnderRoot(self, ):
        fileList = list[str]()
        for root, _, files in os.walk(self.__rootPath, ):
            for file in files:
                fullPath = Path(root, file, ).absolute().as_posix()
                if not self.__pathResolver.isImportantResource(fullPath, ):
                    fileList.append(fullPath)

        managedPaths = set(resourceFile.path.absolute().as_posix() for resourceFile in self.__resources.keys())
        notManagedFiles = set(fileList) - managedPaths
        return [p for p in notManagedFiles]

    def listResources(self, extension: Optional[Iterable[str]] = None, ):
        if extension is None:
            return list(self.__resources.values(), )
        else:
            return [r for rf, r in list(self.__resources.items(), ) if rf.path.suffix in extension]
    