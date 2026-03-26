"""
Proxy models for Machine Learning Studio admin grouping.
These don't create new tables - they just provide a way to register
the same models under a different admin section.
"""

from dose.models import MLEngine, MLTaxonomy, MLDataset, DeepSeekPrompt


class MLEngineProxy(MLEngine):
    """Proxy model for MLEngine - appears in Machine Learning Studio section"""
    class Meta:
        proxy = True
        verbose_name = 'ML Engine'
        verbose_name_plural = 'ML Engines'


class MLTaxonomyProxy(MLTaxonomy):
    """Proxy model for MLTaxonomy - appears in Machine Learning Studio section"""
    class Meta:
        proxy = True
        verbose_name = 'ML Taxonomy'
        verbose_name_plural = 'ML Taxonomies'


class MLDatasetProxy(MLDataset):
    """Proxy model for MLDataset - appears in Machine Learning Studio section"""
    class Meta:
        proxy = True
        verbose_name = 'ML Dataset'
        verbose_name_plural = 'ML Datasets'


class MLPromptProxy(DeepSeekPrompt):
    """Proxy model for DeepSeekPrompt - appears as ML Prompts in Machine Learning Studio section"""
    class Meta:
        proxy = True
        verbose_name = 'ML Prompt'
        verbose_name_plural = 'ML Prompts'
