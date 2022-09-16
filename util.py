import copy
import os

import torch
from cyy_naive_lib.algorithm.mapping_op import get_mapping_values_by_key_order
from cyy_naive_lib.log import get_logger
from cyy_torch_toolbox.dataset import sub_dataset
from cyy_torch_toolbox.inferencer import Inferencer
from cyy_torch_toolbox.ml_type import MachineLearningPhase
from cyy_torch_toolbox.trainer import Trainer


def analysis_contribution(
    contribution_dict: dict, threshold: float
) -> tuple[dict, dict]:
    contribution = torch.Tensor(
        list(get_mapping_values_by_key_order(contribution_dict))
    )
    std, mean = torch.std_mean(contribution)
    max_contribution = torch.max(contribution).item()
    min_contribution = torch.min(contribution).item()

    get_logger().info("std is %s", std)
    get_logger().info("mean is %s", mean)
    get_logger().info("max contribution is %s", max_contribution)
    get_logger().info("min contribution is %s", min_contribution)
    get_logger().info(
        "positive contributions have %s", contribution[contribution >= 0].shape
    )
    get_logger().info(
        "negative contributions have %s", contribution[contribution < 0].shape
    )

    positive_contributions: dict = {
        k: v for k, v in contribution_dict.items() if v > (max_contribution * threshold)
    }
    negative_contributions: dict = {
        k: v for k, v in contribution_dict.items() if v < (min_contribution * threshold)
    }
    return positive_contributions, negative_contributions


def get_instance_statistics(tester: Inferencer, instance_dataset) -> dict:
    tester = copy.deepcopy(tester)
    tester.dataset_collection.transform_dataset(
        MachineLearningPhase.Test, lambda _: instance_dataset
    )
    tester.inference(sample_prob=True)
    return tester.prob_metric.get_prob(1)[0]


def save_training_image(
    save_dir: str, trainer: Trainer, contribution: dict, index: int
) -> None:
    sample_dataset = sub_dataset(trainer.dataset, [index])
    prob_index, prob = get_instance_statistics(
        trainer.get_inferencer(phase=MachineLearningPhase.Test), sample_dataset
    )

    trainer.dataset_util.save_sample_image(
        index=index,
        path=os.path.join(
            save_dir,
            "index_{}_contribution_{}_predicted_class_{}_prob_{}_real_class_{}.jpg".format(
                index,
                contribution[index],
                trainer.dataset_util.get_label_names()[prob_index],
                prob,
                trainer.dataset_util.get_label_names()[sample_dataset[0][1]],
            ),
        ),
    )
