import helper
import compute

import random
from types import SimpleNamespace
from copy import copy
import numpy as np

def main(settings, dataset_number=5, image_size=200, padding=2, n_clusters=None, out_file='../img.png'):
    # Load images and get embeddings from NN
    imgs = helper.get_images(dataset_number)
    embeddings = helper.get_embeddings(dataset_number, imgs)
    print('loaded {} images'.format(len(imgs)))

    if settings.shuffle:
        random.shuffle(imgs)

    # Compute 2D embeddings with MDS
    if settings.no_mds:
        em_2d = np.random.random((len(imgs), 2))
    else:    
        em_2d = compute.mds(embeddings, init=compute.pca(embeddings))

    # Perform clustering
    cluster_centers, labels = compute.k_means(em_2d, k_default=n_clusters)
    print('clusters:', len(cluster_centers))
    print('sizes of clusters: ', end='')
    for l in range(max(labels) + 1):
        print(sum(labels == l), end=', ')
    print()

    # Representative images
    silhouettes = compute.get_silhouettes(em_2d, labels)
    representative = compute.get_representative(em_2d, cluster_centers, labels, silhouettes)

    # Sizes and positions of the images
    ratios = helper.get_image_size_ratios(imgs)
    sizes = compute.get_sizes(image_size, em_2d, ratios, cluster_centers, labels, representative)
    positions = compute.get_positions(em_2d, image_size)

    # Expand as long as overlaps occur - gradually increase space between images
    iters = 0
    while compute.overlap(positions, sizes, padding):
        positions *= 1.05
        iters += 1
    print('overlap resolved in {} iterations'.format(iters))

    dists = [compute.get_distances(positions)]

    # Overlapping resolved, now "shrink" towards representative images
    if not settings.no_intra:
        positions = compute.shrink_intra(positions, sizes, representative, labels, padding)
        dists.append(compute.get_distances(positions))

    if not settings.no_inter:
        # Move clusters closer together by same factor
        positions = compute.shrink_inter1(positions, sizes, representative, labels, padding)
        dists.append(compute.get_distances(positions))

        # Move clusters closer together separately by different factors
        positions = compute.shrink_inter2(positions, sizes, representative, labels, padding)
        dists.append(compute.get_distances(positions))

    if not settings.no_xy:
        # Shrink by x and y separately
        positions = compute.shrink_xy(positions, sizes, representative, labels, padding)
        dists.append(compute.get_distances(positions))

    if not settings.no_shake:
        # "Shake" images with small offsets
        for _ in range(10):
            positions = compute.shrink_with_shaking(positions, sizes, padding)
        dists.append(compute.get_distances(positions))

    if not settings.no_final:
        # Shrink to finalize positions
        positions = compute.shrink_xy(positions, sizes, representative, labels, padding)
        dists.append(compute.get_distances(positions))
        positions = compute.shrink_xy(positions, sizes, representative, labels, padding, smaller=True)
        dists.append(compute.get_distances(positions))
        
        if not settings.no_inter:
            positions = compute.shrink_inter2(positions, sizes, representative, labels, padding)
            dists.append(compute.get_distances(positions))

    im = helper.plot(imgs, positions, sizes)
    im.save(out_file)
    # helper.plot_clusters(em_2d, cluster_centers, labels, representative)

    scores = list(map(lambda d: compute.compare_distances(dists[0], d), dists))

    print('\nscores:')
    for i, s in enumerate(scores[1:]):
        print('{:.3f},'.format(s), end=' ')


if __name__ == '__main__':
    
    default_settings = {
        'default': False,
        'shuffle': False, 
        'no_mds': False, 
        'no_inter': False, 
        'no_intra': False, 
        'no_xy': False,
        'no_shake': False,
        'no_final': False
    }
    
    for setting in default_settings:
        settings = copy(default_settings)
        settings[setting] = True
        
        for dataset, clusters in [(2, None), (4, None), (5, None), (7, None), (9, 3)]:
            main(SimpleNamespace(**settings),
                dataset_number=dataset, 
                n_clusters=clusters, 
                out_file=f'../generated/{dataset}_{setting}.png')