from torch.utils.data import Dataset
import numpy as np
import random
import torch

class JitterTransform:
	def __init__(self, jitter_range=0.1):
		self.jitter_range = jitter_range
	def __call__(self, X):
		return X + torch.randn_like(X) * self.jitter_range

class ScaleTransform:
	def __init__(self, scale_range=0.1):
		self.scale_range = scale_range
	def __call__(self, X):
		return X * ((random.random()*2-1)*self.scale_range+1)

class ClusterDataset(Dataset):
	def __init__(self, dataframe, features, cluster_ids=None, feature_divs=None, transforms=[]):
		super().__init__() 
		self.standard_feature_divs = {'estar':89000, 'lzstar':2000, 'lxstar':2000, 'lystar':2000, 'jzstar':2000, 'jrstar':2000, 'eccstar':1, 'rstar':4, 'feH':1, 'mgfe':0.5, 'xstar':10, 'ystar':10, 'zstar':10, 'vxstar':200, 'vystar':200, 'vzstar':200, 'vrstar':200, 'vphistar':200, 'vrstar':200, 'vthetastar':200}
		if feature_divs is None:
			self.feature_divs = torch.tensor([self.standard_feature_divs[feature] for feature in features])
		else:
			self.feature_divs = torch.tensor([feature_divs[feature].to_numpy()[0] for feature in features])
		if isinstance(features, np.ndarray):
			self.features = torch.tensor(features).float()
		else:
			self.features = torch.tensor(dataframe[features].to_numpy()).float()
		self.features /= self.feature_divs[None,...]
		if cluster_ids is None:
			self.labels = None
		elif isinstance(cluster_ids, str):
			self.labels = torch.tensor(dataframe[cluster_ids].to_numpy()).long()
		else:
			self.labels = torch.tensor(cluster_ids).long()
		if self.labels is not None:
			self.labels -= torch.min(self.labels)
		assert self.labels is None or len(self.labels) == self.features.shape[0]
		self.transforms = transforms

	def __len__(self):
		return self.features.shape[0]

	def __getitem__(self, idx):
		feature = self.features[idx]
		for transform in self.transforms:
			feature = transform(feature)
		if self.labels is None:
			return feature, None
		else:
			return feature, self.labels[idx]

class ContrastDataset(Dataset):
	def __init__(self, dataframe, features, cluster_ids, feature_divs=None, positive_percent=None, transforms=[]):
		super().__init__()
		if positive_percent is None:
			self.positive_percent = 0.3
		else:
			self.positive_percent = positive_percent
		self.standard_feature_divs = {'estar':1e5, 'lzstar':2000, 'lxstar':2000, 'lystar':2000, 'jzstar':2000, 'jrstar':2000, 'eccstar':1, 'rstar':4, 'feH':1, 'mgfe':0.5, 'xstar':10, 'ystar':10, 'zstar':10, 'vxstar':200, 'vystar':200, 'vzstar':200, 'vrstar':200, 'vphistar':200, 'vrstar':200, 'vthetastar':200}
		if feature_divs is None:
			self.feature_divs = torch.tensor([self.standard_feature_divs[feature] for feature in features])
		else:
			self.feature_divs = torch.tensor([feature_divs[feature].to_numpy()[0] for feature in features])
		if isinstance(features, np.ndarray):
			self.features = torch.tensor(features).float()
		else:
			self.features = torch.tensor(dataframe[features].to_numpy()).float()
		self.features /= self.feature_divs[None,...]
		if cluster_ids is None:
			self.labels = None
		elif isinstance(cluster_ids, str):
			self.labels = torch.tensor(dataframe[cluster_ids].to_numpy()).long()
		else:
			self.labels = torch.tensor(cluster_ids).long()
		if self.labels is not None:
			self.labels -= torch.min(self.labels)

		self.cluster_ids = list(set([label.item() for label in self.labels]))
		self.clusters = {}
		for i in range(len(self.labels)):
			if self.labels[i].item() not in self.clusters:
				self.clusters[self.labels[i].item()] = []
			self.clusters[self.labels[i].item()].append(i)
		self.transforms = transforms
		assert self.labels is None or len(self.labels) == self.features.shape[0]

	def global_transform(self, transforms=None):
		if transforms is None:
			transforms = self.transforms
		for cluster_id in self.cluster_ids:
			features = self.features[torch.tensor(self.clusters[cluster_id])]
			for transform in transforms:
				features = transform(features)
			self.features[torch.tensor(self.clusters[cluster_id])] = features

	def __len__(self):
		return self.features.shape[0]

	def __getitem__(self, idx):
		cluster_id = self.labels[idx].item()
		if random.random() < self.positive_percent:
			cluster_id = self.labels[idx].item()
		else:
			cluster_id = self.cluster_ids[random.randint(0, len(self.cluster_ids)-1)]
		other_id = self.clusters[cluster_id][random.randint(0, len(self.clusters[cluster_id])-1)]
		feature = self.features[idx]
		for transform in self.transforms:
			feature = transform(feature)
		o_feature = self.features[other_id]
		for transform in self.transforms:
			o_feature = transform(o_feature)
		return feature, o_feature, self.labels[idx], self.labels[other_id]

