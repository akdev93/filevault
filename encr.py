from pathlib import Path
import os
import subprocess
import secrets


class EncryptionException(Exception):

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class Encryptor:

    
    def __init__(self, keyAccessor):
        self.key = keyAccessor()

        
    def encryptFile(self, file, outputDirectory):

        outputFileName = f'{Path(file).name}.7z'

        self.encryptFiles([file], outputFileName, outputDirectory)


    def encryptFile2(self, file, outputDirectory, outputFile):

        outputFileName = f'{outputFile}'

        self.encryptFiles([file], outputFileName, outputDirectory)

        
    def encryptFiles(self, files, outputFileName, outputDirectory):

        command_args = ['7z.exe', 'a', f'-p{self.key}', "-aoa", f'{outputDirectory}/{outputFileName}']
        for f in files:
            command_args.append(f)

        self._executeHostCommand(command_args)


    def decryptFile(self, file, outputDirectory):
        
        fileName = Path(file).name

        command_args = ['7z.exe', 'e', f'-p{self.key}', f'-o{outputDirectory}', "-aoa", file]
        self._executeHostCommand(command_args)


    def _executeHostCommand(self, command_args):
        completedProcess = subprocess.run(command_args, capture_output=True, shell = True)
        print(completedProcess.stdout)
        print(completedProcess.stderr)
        print(completedProcess.returncode)
        if(completedProcess.returncode != 0):
            raise EncryptionException(completedProcess.stderr)
       


class CompositeEncryptor:

   def __init__(self, masterKeyAccessor, secondaryKeyAccessor):
       self.encryptor = Encryptor(masterKeyAccessor)
       self.secondaryKeyAccessor = secondaryKeyAccessor

   
   def encryptFile(self, file, outputDirectory):
       fileName = Path(file).name
       fileDir = Path(file).parent.as_posix()
       generatedKey = KeyGenerators.randomKey(2048)
       keyFile = f'{file}.key'
       
       with open(f'{file}.key', 'w') as f:
           f.write(generatedKey)
       
       encryptor = Encryptor( lambda: KeyGenerators.fromFile(keyFile))
       encryptor.encryptFile(file, fileDir)

       keyEncryptor = Encryptor(lambda: self.secondaryKeyAccessor(fileName))
       keyEncryptor.encryptFile(keyFile, fileDir)
       self.encryptor.encryptFiles([f'{file}.7z', f'{keyFile}.7z'], f'{fileName}.encr.7z', outputDirectory)
       Path(keyFile).unlink()
       Path(f'{keyFile}.7z').unlink()
       Path(f'{file}.7z').unlink()
    

   def decryptFile(self, file, outputFile):
       
       sourceFileName = file.replace(".encr.7z","")
       encryptedSourceFile = f'{sourceFileName}.7z'
       encryptedKeyFile = f'{sourceFileName}.key.7z'
       keyFile = f'{sourceFileName}.key'

       dir = Path(file).parent.as_posix()


       self.encryptor.decryptFile(file, dir)
       keyFileDecryptor = Encryptor(lambda: self.secondaryKeyAccessor(Path(sourceFileName).name))
       keyFileDecryptor.decryptFile(encryptedKeyFile, dir)

       encryptor = Encryptor(lambda: KeyGenerators.fromFile(keyFile))
       encryptor.decryptFile(encryptedSourceFile, dir)
       Path(encryptedSourceFile).unlink()
       Path(encryptedKeyFile).unlink()
       Path(keyFile).unlink()


class KeyGenerators:

    def fromFile(keyFile):
        with open(keyFile) as f:
            return f.read().rstrip()

    def randomKey(size):
        return secrets.token_urlsafe(size)



