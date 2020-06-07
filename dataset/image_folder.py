###############################################################################
import torch.utils.data as data
from PIL import Image
import os

IMG_EXTENSIONS = [
    '.jpg', '.JPG', '.jpeg', '.JPEG',
    '.png', '.PNG', '.ppm', '.PPM', '.bmp', '.BMP', '.tiff'
]


def is_image_file(filename):
    return any(filename.endswith(extension) for extension in IMG_EXTENSIONS)

def make_dataset(dir):
    images = []
    assert os.path.isdir(dir), '%s is not a valid directory' % dir

    #f = dir.split('/')[-1].split('_')[-1]
    # print (dir, f)
    dirs= os.listdir(dir)
    for img in dirs:
        if '.'+ img.split('.')[-1] in IMG_EXTENSIONS:
            path = os.path.join(dir, img)
            #print(path)
            images.append(path)
    return images

def make_dataset_test(dir):
    images = []
    assert os.path.isdir(dir), '%s is not a valid directory' % dir

    f = dir.split('/')[-1].split('_')[-1]
    for i in range(len([name for name in os.listdir(dir) if os.path.isfile(os.path.join(dir, name))])):
        if f == 'label' or f == 'labelref':
            img = str(i) + '.png'
        else:
            img = str(i) + '.jpg'
        path = os.path.join(dir, img)
        #print(path)
        images.append(path)
    return images

def default_loader(path):
    return Image.open(path).convert('RGB')


class ImageFolder(data.Dataset):

    def __init__(self, root, transform=None, return_paths=False,
                 loader=default_loader):
        imgs = make_dataset(root)
        if len(imgs) == 0:
            raise(RuntimeError("Found 0 images in: " + root + "\n"
                               "Supported image extensions are: " +
                               ",".join(IMG_EXTENSIONS)))

        self.root = root
        self.imgs = imgs
        self.transform = transform
        self.return_paths = return_paths
        self.loader = loader

    def __getitem__(self, index):
        path = self.imgs[index]
        img = self.loader(path)
        if self.transform is not None:
            img = self.transform(img)
        if self.return_paths:
            return img, path
        else:
            return img

    def __len__(self):
        return len(self.imgs)