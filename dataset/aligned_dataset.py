import os.path
import torch.utils.data as data
from dataset.base_dataset import BaseDataset, get_params, get_transform, normalize
from dataset.image_folder import make_dataset, make_dataset_test
from PIL import Image
import torch
import json
import numpy as np
import os.path as osp
from PIL import ImageDraw
from models.SingleHumanParser.inference1 import get_parser
import cv2 as cv

class AlignedDataset(BaseDataset):
    def initialize(self, opt):
        self.opt = opt
        self.root = opt.dataroot    
        self.diction={}
        ### input A (label maps)
        if opt.isTrain or opt.use_encoded_image:
            dir_A = '_A' if self.opt.label_nc == 0 else '_label'
            self.dir_A = os.path.join(opt.dataroot, opt.phase, opt.phase + dir_A)
            self.A_paths = sorted(make_dataset(self.dir_A))
            self.AR_paths = make_dataset(self.dir_A)

        self.fine_height=256
        self.fine_width=192
        self.radius=5
        ### input A sample (label maps)
        if not (opt.isTrain or opt.use_encoded_image):
            dir_A = '_A' if self.opt.label_nc == 0 else '_label'
            self.dir_A = os.path.join(opt.dataroot, opt.phase, opt.phase + dir_A)
            self.A_paths = sorted(make_dataset(self.dir_A))
            dir_AR = '_AR' if self.opt.label_nc == 0 else '_labelref'
            self.dir_AR = os.path.join(opt.dataroot, opt.phase, opt.phase + dir_AR)
            self.AR_paths = sorted(make_dataset(self.dir_AR))

        ### input B (real images)
        dir_B = '_B' if self.opt.label_nc == 0 else '_img'
        self.dir_B = os.path.join(opt.dataroot, opt.phase, opt.phase + dir_B)
        self.B_paths = sorted(make_dataset(self.dir_B))
        self.BR_paths = sorted(make_dataset(self.dir_B))

        ### input C (cloth images)
        dir_C = '_color'
        self.dir_C = os.path.join(opt.dataroot, opt.phase, opt.phase + dir_C)
        self.C_paths = sorted(make_dataset(self.dir_C))
        self.CR_paths = make_dataset(self.dir_C)

        ### input E (edge_maps)
        dir_E = '_edge'
        self.dir_E = os.path.join(opt.dataroot, opt.phase, opt.phase + dir_E)
        self.E_paths = sorted(make_dataset(self.dir_E))
        self.ER_paths = make_dataset(self.dir_E)


        self.dataset_size = len(self.A_paths)
        self.build_index(self.B_paths)

        ### input E (edge_maps)
        if opt.isTrain or opt.use_encoded_image:
            dir_E = '_edge'
            self.dir_E = os.path.join(opt.dataroot, opt.phase, opt.phase + dir_E)
            self.E_paths = sorted(make_dataset(self.dir_E))
            self.ER_paths = make_dataset(self.dir_E)

        ### input M (masks)
        if opt.isTrain or opt.use_encoded_image:
            dir_M = '_mask'
            self.dir_M = os.path.join(opt.dataroot, opt.phase, opt.phase + dir_M)
            self.M_paths = sorted(make_dataset(self.dir_M))
            self.MR_paths = make_dataset(self.dir_M)

        ### input MC(color_masks)
        if opt.isTrain or opt.use_encoded_image:
            dir_MC = '_colormask'
            self.dir_MC = os.path.join(opt.dataroot, opt.phase, opt.phase + dir_MC)
            self.MC_paths = sorted(make_dataset(self.dir_MC))
            self.MCR_paths = make_dataset(self.dir_MC)
        ### input C(color)
        if opt.isTrain or opt.use_encoded_image:
            dir_C = '_color'
            self.dir_C = os.path.join(opt.dataroot, opt.phase, opt.phase + dir_C)
            self.C_paths = sorted(make_dataset(self.dir_C))
            self.CR_paths = make_dataset(self.dir_C)
        # self.build_index(self.C_paths)

        ### input A sample (label maps)
        if not (opt.isTrain or opt.use_encoded_image):
            dir_A = '_A' if self.opt.label_nc == 0 else '_label'
            self.dir_A = os.path.join(opt.dataroot, opt.phase, opt.phase + dir_A)
            self.A_paths = sorted(make_dataset(self.dir_A))
    def random_sample(self,item):
        name = item.split('/')[-1]
        name = name.split('-')[0]
        lst=self.diction[name]
        new_lst=[]
        for dir in lst:
            if dir != item:
                new_lst.append(dir)
        return new_lst[np.random.randint(len(new_lst))]
    def build_index(self,dirs):
        for k,dir in enumerate(dirs):
            name=dir.split('/')[-1]
            name=name.split('-')[0]

            # print(name)
            for k,d in enumerate(dirs[max(k-20,0):k+20]):
                if name in d:
                    if name not in self.diction.keys():
                        self.diction[name]=[]
                        self.diction[name].append(d)
                    else:
                        self.diction[name].append(d)


    def __getitem__(self, index):
        train_mask=9600
        ### input A (label maps)
        box=[]
        # for k,x in enumerate(self.A_paths):
        #     if '000386' in x :
        #         index=k
        #         break
        test=np.random.randint(len(self.A_paths))
        # for k, s in enumerate(self.B_paths):
        #    if '006581' in s:
        #        sample = k
        #        break
        A_path = self.A_paths[index]
        AR_path = self.AR_paths[index]
        A = Image.open(A_path).convert('L')
        AR = Image.open(AR_path).convert('L')

        params = get_params(self.opt, A.size)
        if self.opt.label_nc == 0:
            transform_A = get_transform(self.opt, params)
            A_tensor = transform_A(A.convert('RGB'))
            print(A.size())
            AR_tensor = transform_A(AR.convert('RGB'))
        else:
            transform_A = get_transform(self.opt, params, method=Image.NEAREST, normalize=False)
            A_tensor = transform_A(A) * 255.0
            AR_tensor = transform_A(AR) * 255.0
        B_tensor = inst_tensor = feat_tensor = 0
        ### input B (real images)

        B_path = self.B_paths[index]
        name=B_path.split('/')[-1]


        BR_path = self.BR_paths[index]
        B = Image.open(B_path).convert('RGB')
        BR = Image.open(BR_path).convert('RGB')
        transform_B = get_transform(self.opt, params)      
        B_tensor = transform_B(B)
        BR_tensor = transform_B(BR)

        ### input M (masks)
        M_path = B_path#self.M_paths[np.random.randint(1)]
        MR_path = B_path#self.MR_paths[np.random.randint(1)]
        M = Image.open(M_path).convert('L')
        MR = Image.open(MR_path).convert('L')
        M_tensor = transform_A(MR)

        ### input_MC (colorMasks)
        MC_path = B_path#self.MC_paths[1]
        MCR_path = B_path#self.MCR_paths[1]
        MCR = Image.open(MCR_path).convert('L')
        MC_tensor = transform_A(MCR)

        ### input_C (color)
        # print(self.C_paths)
        C_path = self.C_paths[test]
        C = Image.open(C_path).convert('RGB')
        C_tensor = transform_B(C)


        ##Edge
        E_path = self.E_paths[test]
        # print(E_path)
        E = Image.open(E_path).convert('L')
        E_tensor = transform_A(E)


        ##Pose
        pose_name =B_path.replace('.jpg', '_keypoints.json').replace('_img','_pose')
        with open(osp.join(pose_name), 'r') as f:
            pose_label = json.load(f)
            pose_data = pose_label['people'][0]['pose_keypoints']
            pose_data = np.array(pose_data)
            pose_data = pose_data.reshape((-1,3))

        point_num = pose_data.shape[0]
        pose_map = torch.zeros(point_num, self.fine_height, self.fine_width)
        r = self.radius
        im_pose = Image.new('L', (self.fine_width, self.fine_height))
        pose_draw = ImageDraw.Draw(im_pose)
        for i in range(point_num):
            one_map = Image.new('L', (self.fine_width, self.fine_height))
            draw = ImageDraw.Draw(one_map)
            pointx = pose_data[i,0]
            pointy = pose_data[i,1]
            if pointx > 1 and pointy > 1:
                draw.rectangle((pointx-r, pointy-r, pointx+r, pointy+r), 'white', 'white')
                pose_draw.rectangle((pointx-r, pointy-r, pointx+r, pointy+r), 'white', 'white')
            one_map = transform_B(one_map.convert('RGB'))
            pose_map[i] = one_map[0]
        P_tensor=pose_map
        if self.opt.isTrain:
            input_dict = { 'label': A_tensor, 'label_ref': AR_tensor, 'image': B_tensor, 'image_ref': BR_tensor, 'path': A_path, 'path_ref': AR_path,
                            'edge': E_tensor,'color': C_tensor, 'mask': M_tensor, 'colormask': MC_tensor,'pose':P_tensor,'name':name
                          }
        else:
            input_dict = {'label': A_tensor, 'label_ref': AR_tensor, 'image': B_tensor, 'edge': E_tensor,'color': C_tensor, 'image_ref': BR_tensor, 'path': A_path, 'path_ref': AR_path, 'pose':P_tensor, 'name':name}

        return input_dict

    def __len__(self):
        return len(self.A_paths) // self.opt.batchSize * self.opt.batchSize

    def name(self):
        return 'AlignedDataset'


#Get the mask of an cloth item

def get_item_mask(img):
  img = cv.cvtColor(img, cv.COLOR_RGB2LAB)
  mask = img[:,:,0]
  ret,img_th = cv.threshold(mask,0,255,cv.THRESH_BINARY_INV+cv.THRESH_OTSU)
  # Copy the thresholded image.
  img_floodfill = img_th.copy()

  # Mask used to flood filling.
  # Notice the size needs to be 2 pixels than the image.
  h, w = img_floodfill.shape[:2]
  mask = np.zeros((h+2, w+2), np.uint8)
  # Floodfill from point (0, 0)
  cv.floodFill(img_floodfill, mask, (0,0), 255);
  # Invert floodfilled image
  img_floodfill_inv = cv.bitwise_not(img_floodfill)
  # Combine the two images to get the foreground.
  img_out = img_th | img_floodfill_inv
  return img_out


class my_Dataset(data.Dataset):
    def __init__(self, opt, name, person_path, cloth_path, pose_path, parser_path = None, cloth_mask_path = None, from_user = True):
        super(my_Dataset, self).__init__()
        self.opt = opt
        self.person_path = person_path
        self.cloth_path = cloth_path
        self.parser_path = parser_path
        self.pose_path = pose_path
        self.cloth_mask_path = cloth_mask_path
        self.from_user = from_user
        self.name = name


    def __getitem__(self, index):
        person_path = self.person_path
        cloth_path = self. cloth_path
        parser_path = self.parser_path
        pose_path = self.pose_path
        cloth_mask_path  = self.cloth_mask_path
        opt = self.opt

        person = Image.open(person_path).convert('RGB')
        params = get_params(opt, person.size)
        transform_B = get_transform(opt, params)
        person_tensor = transform_B(person)
        
        parser = Image.open(parser_path).convert('L')

        
        if opt.label_nc == 0:
            transform_A = get_transform(opt, params)
            parser_tensor = transform_A(parser.convert('RGB'))
        else:
            transform_A = get_transform(opt, params, method=Image.NEAREST, normalize=False)
            parser_tensor = transform_A(parser) * 255.0


        cloth = Image.open(cloth_path).convert('RGB')
        cloth_tensor = transform_B(cloth)

        if self.from_user:
            cloth_mask = get_item_mask(cv.imread(cloth_path))
            cloth_mask = Image.fromarray(cloth_mask).convert('L')
        else:
            cloth_mask = Image.open(cloth_mask_path).convert('L')
        cloth_mask_tensor = transform_A(cloth_mask)

        ##Pose
        with open(osp.join(pose_path), 'r') as f:
            pose_label = json.load(f)
            if self.from_user:
                pose_data = pose_label['people'][0]['pose_keypoints_2d']
            else:
                pose_data = pose_label['people'][0]['pose_keypoints']
            pose_data = np.array(pose_data)
            pose_data = pose_data.reshape((-1, 3))

        fine_height = 256
        fine_width = 192
        r = 5

        point_num = pose_data.shape[0]
        pose_map = torch.zeros(point_num, fine_height, fine_width)
        im_pose = Image.new('L', (fine_width, fine_height))
        pose_draw = ImageDraw.Draw(im_pose)
        for i in range(point_num):
            one_map = Image.new('L', (fine_width, fine_height))
            draw = ImageDraw.Draw(one_map)
            pointx = pose_data[i, 0]
            pointy = pose_data[i, 1]
            if pointx > 1 and pointy > 1:
                draw.rectangle((pointx - r, pointy - r, pointx + r, pointy + r), 'white', 'white')
                pose_draw.rectangle((pointx - r, pointy - r, pointx + r, pointy + r), 'white', 'white')
            one_map = transform_B(one_map.convert('RGB'))
            pose_map[i] = one_map[0]
        pose_tensor = pose_map

        name = person_path.split('/')[-1]
        input_dict = {'parser': parser_tensor, 'label_ref': parser_tensor, 'person': person_tensor, 'cloth_mask': cloth_mask_tensor,
                          'cloth': cloth_tensor, 'image_ref': person_tensor, 'path': parser_path, 'path_ref': parser_path,
                          'pose': pose_tensor, 'name': name}
        return input_dict

    def __len__(self):
        return 1
