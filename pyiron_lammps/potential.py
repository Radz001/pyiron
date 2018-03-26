# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

from __future__ import print_function
import posixpath
import pandas as pd
import shutil
import os
from pyiron_base.core.settings.generic import Settings
from pyiron_base.objects.generic.parameters import GenericParameters
from pyiron_atomistics.hamilton.potentials import PotentialAbstract

__author__ = "Joerg Neugebauer, Sudarsan Surendralal, Jan Janssen"
__copyright__ = "Copyright 2017, Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department"
__version__ = "1.0"
__maintainer__ = "Sudarsan Surendralal"
__email__ = "surendralal@mpie.de"
__status__ = "production"
__date__ = "Sep 1, 2017"

s = Settings()


class LammpsPotential(GenericParameters):

    """
    This module helps write commands which help in the control of parameters related to the potential used in LAMMPS
    simulations
    """

    def __init__(self, input_file_name=None):
        super(LammpsPotential, self).__init__(input_file_name=input_file_name,
                                              table_name="potential_inp",
                                              comment_char="#")
        self._potential = None
        self._attributes = {}
        self._df = None

    @property
    def df(self):
        return self._df

    @df.setter
    def df(self, new_dataframe):
        self._df = new_dataframe
        # ToDo: In future lammps should also support more than one potential file - that is currently not implemented.
        self.load_string(''.join(list(new_dataframe['Config'])[0]))

    def remove_structure_block(self):
        self.remove_keys(["units"])
        self.remove_keys(["atom_style"])
        self.remove_keys(["dimension"])

    @property
    def files(self):
        pot_file_lst = {}
        for resource_path in s.resource_paths:
            if os.path.exists(os.path.join(resource_path, 'pyiron_lammps', 'potentials')):
                resource_path = os.path.join(resource_path, 'pyiron_lammps', 'potentials')
            if 'potentials' in resource_path:
                for pot_file in list(self._df['Filename'])[0]:
                    if os.path.exists(os.path.join(resource_path, pot_file)):
                        pot_file_lst[pot_file] = os.path.join(resource_path, pot_file)
                    if set(list(self._df['Filename'])[0]) == set(pot_file_lst.keys()):
                        return list(pot_file_lst.values())
        return [posixpath.join(s.path_potentials, file) for file in list(self._df['Filename'])[0]]

    def copy_pot_files(self, working_directory):
        _ = [shutil.copy(path_pot, working_directory) for path_pot in self.files]

    def get_element_lst(self):
        return list(self._df['Species'])[0]

    def to_hdf(self, hdf, group_name=None):
        if self._df is not None:
            with hdf.open('potential') as hdf_pot:
                hdf_pot['Config'] = self._df['Config'].values[0]
                hdf_pot['Filename'] = self._df['Filename'].values[0]
                hdf_pot['Name'] = self._df['Name'].values[0]
                hdf_pot['Model'] = self._df['Model'].values[0]
                hdf_pot['Species'] = self._df['Species'].values[0]
        super(LammpsPotential, self).to_hdf(hdf, group_name=group_name)

    def from_hdf(self, hdf, group_name=None):
        with hdf.open('potential') as hdf_pot:
            try:
                self._df = pd.DataFrame({'Config': [hdf_pot['Config']],
                                         'Filename': [hdf_pot['Filename']],
                                         'Name': [hdf_pot['Name']],
                                         'Model': [hdf_pot['Model']],
                                         'Species': [hdf_pot['Species']]})
            except ValueError:
                pass
        super(LammpsPotential, self).from_hdf(hdf, group_name=group_name)


class LammpsPotentialFile(PotentialAbstract):
    """
    The Potential class is derived from the PotentialAbstract class, but instead of loading the potentials from a list,
    the potentials are loaded from a file.

    Args:
        potential_df:
        default_df:
        selected_atoms:
    """

    def __init__(self, potential_df=None, default_df=None, selected_atoms=None):
        if potential_df is None:
            potential_df = self._get_potential_df(plugin_name='pyiron_lammps',
                                                  file_name_lst={'potentials_lammps.csv'},
                                                  backward_compatibility_name='lammpspotentials')
        super(LammpsPotentialFile, self).__init__(potential_df=potential_df, default_df=default_df,
                                                  selected_atoms=selected_atoms)

    def default(self):
        if self._default_df is not None:
            atoms_str = '_'.join(sorted(self._selected_atoms))
            return self._default_df[(self._default_df['Name'] == self._default_df.loc[atoms_str].values[0])]
        return None

    def find_default(self, element):
        """
        Find the potentials

        Args:
            element (set, str): element or set of elements for which you want the possible LAMMPS potentials
            path (bool): choose whether to return the full path to the potential or just the potential name

        Returns:
            list: of possible potentials for the element or the combination of elements

        """
        if isinstance(element, set):
            element = element
        elif isinstance(element, list):
            element = set(element)
        elif isinstance(element, str):
            element = set([element])
        else:
            raise TypeError('Only, str, list and set supported!')
        element_lst = list(element)
        if self._default_df is not None:
            merged_lst = list(set(self._selected_atoms + element_lst))
            atoms_str = '_'.join(sorted(merged_lst))
            return self._default_df[(self._default_df['Name'] == self._default_df.loc[atoms_str].values[0])]
        return None

    def __getitem__(self, item):
        potential_df = self.find(element=item)
        selected_atoms = self._selected_atoms + [item]
        return LammpsPotentialFile(potential_df=potential_df, default_df=self._default_df, selected_atoms=selected_atoms)
